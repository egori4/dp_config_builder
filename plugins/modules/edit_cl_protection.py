# plugins/modules/edit_cl_protection.py
"""
Ansible module to edit existing DefensePro connection limit protection subprofiles via Radware CyberController API.

This module allows you to modify existing connection limit protection subprofiles on Radware DefensePro devices
using the Radware CyberController API. It requires the protection index which can be obtained from the DefensePro UI
or by running get_cl_protections.yml playbook.

Classes:
  None

Functions:
  run_module():
    Main logic for the module. Handles argument parsing, logging, API request construction,
    and response handling. Supports check mode.

  main():
    Entrypoint for the module execution.

Module Arguments:
  provider (dict): Connection parameters for Radware CyberController.
    - cc_ip (str): CyberController IP address.
    - username (str): Username for authentication.
    - password (str): Password for authentication.
    - log_level (str, optional): Logging verbosity (default: 'disabled').
  dp_ip (str): Target DefensePro device IP address.
  protection_index (int): Index of the existing protection to edit.
  protection_name (str, optional): New name for the connection limit protection.
  protocol (str, optional): Protocol type.
  threshold (str, optional): Connection limit threshold.
  app_port_group (str, optional): Application port group.
  tracking_type (str, optional): Tracking type.
  action (str, optional): Action mode.
  packet_report (str, optional): Packet report setting.
  protection_type (str, optional): Protection type.

Returns:
  response (dict): API response from Radware CyberController.
  changed (bool): Indicates if any change was made.
  debug_info (dict): Debug information including request and response details.

Exceptions:
  Raises Exception if API response is invalid or if any error occurs during execution.

References:
  - Radware CyberController API documentation for connection limit protection management.
  - AnsibleModule documentation: https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html
  - RadwareCC utility: ansible.module_utils.radware_cc
  - Logger utility: ansible.module_utils.logger

Note:
  The module supports check mode and provides detailed logging if log_level is set.
  Only specify parameters you want to change - others will remain unchanged on the device.
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: edit_cl_protection
short_description: Edit existing DefensePro connection limit protection subprofiles
description:
  - Edits existing connection limit protection subprofiles on Radware DefensePro via Radware CC API.
  - Uses PUT method to modify existing protections by index.
  - Only specify parameters you want to change - others remain unchanged.
options:
  provider:
    description:
      - Dictionary with connection parameters.
    type: dict
    required: true
    suboptions:
      cc_ip:
        description: CC IP address
        type: str
        required: true
      username:
        type: str
        required: true
      password:
        type: str
        required: true
  dp_ip:
    type: str
    required: true
  protection_index:
    description:
      - Index of the existing protection to edit
      - Can be found in DefensePro UI or by running get_cl_protections.yml
    type: int
    required: true
  protection_name:
    description:
      - Name of the connection limit protection (optional - only if changing)
    type: str
    required: false
  protocol:
    description:
      - Protocol type for connection limit protection (optional - only if changing)
    type: str
    choices: ['tcp', 'udp']
    required: false
  threshold:
    description:
      - Connection limit threshold (optional - only if changing)
    type: str
    required: false
  app_port_group:
    description:
      - Application port group for the connection limit attack (optional - only if changing)
      - Common values include http, https, dns, ftp, smtp, imap
      - Leave empty for all ports
    type: str
    required: false
  tracking_type:
    description:
      - Type of connection counting for connection limiting (optional - only if changing)
    type: str
    choices: ['src_ip', 'dst_ip', 'src_and_dest_ip', 'dst_ip_and_port']
    required: false
  action:
    description:
      - Action to take when connection limit is exceeded (optional - only if changing)
    type: str
    choices: ['report_only', 'drop']
    required: false
  packet_report:
    description:
      - Per-attack packet report setting (optional - only if changing)
    type: str
    choices: ['enable', 'disable']
    required: false
  protection_type:
    description:
      - Type of connection limit protection detection (optional - only if changing)
    type: str
    choices: ['cps', 'concurrent_connections']
    required: false
'''

EXAMPLES = r'''
# Example of how the module is called within a playbook task
# Variables come from vars/edit_cl_vars.yml file
- name: "Edit connection limit protection {{ item.1.protection_name | default('index ' + item.1.protection_index|string) }} on {{ item.0 }}"
  edit_cl_protection:
    provider: "{{ cc }}"
    dp_ip: "{{ item.0 }}"
    protection_index: "{{ item.1.protection_index }}"
    protection_name: "{{ item.1.protection_name | default(omit) }}"
    protocol: "{{ item.1.protocol | default(omit) }}"
    threshold: "{{ item.1.threshold | default(omit) }}"
    app_port_group: "{{ item.1.app_port_group | default(omit) }}"
    tracking_type: "{{ item.1.tracking_type | default(omit) }}"
    action: "{{ item.1.action | default(omit) }}"
    packet_report: "{{ item.1.packet_report | default(omit) }}"
    protection_type: "{{ item.1.protection_type | default(omit) }}"

# Direct module call example (for testing or standalone use)
- name: Edit a specific connection limit protection threshold
  edit_cl_protection:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.32
    protection_index: 450096
    threshold: '200'
    action: 'report_only'
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
changed:
  description: Indicates if the protection was modified
  type: bool
debug_info:
  description: Debug information including request details
  type: dict
'''

def run_module():
    # User-friendly value mappings based on MIB definitions
    PROTOCOL_MAP = {
        'tcp': '2',      # tcp (2)
        'udp': '3'       # udp (3)
    }
    
    ATTACK_TYPE_MAP = {
        'cps': '1',                    # cps(1)
        'concurrent_connections': '2'   # concurrentconnection(2)
    }
    
    TRACKING_TYPE_MAP = {
        'src_ip': '2',              # Source IP tracking (2)
        'dst_ip': '3',              # Destination IP tracking (3)  
        'src_and_dest_ip': '4',     # Both source and destination IP (4)
        'dst_ip_and_port': '5'      # Destination IP and port (5)
    }
    
    ACTION_MAP = {
        'report_only': '0',         # report-only(0) 
        'drop': '10'                # drop(10)
    }
    
    PACKET_REPORT_MAP = {
        'enable': '1',              # enable(1)
        'disable': '2'              # disable(2)
    }

    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        protection_index=dict(type='int', required=True),
        protection_name=dict(type='str', required=False),
        protocol=dict(type='str', required=False, choices=['tcp', 'udp']),
        threshold=dict(type='str', required=False),
        app_port_group=dict(type='str', required=False),
        tracking_type=dict(type='str', required=False,
                          choices=['src_ip', 'dst_ip', 'src_and_dest_ip', 'dst_ip_and_port']),
        action=dict(type='str', required=False, choices=['report_only', 'drop']),
        packet_report=dict(type='str', required=False, choices=['enable', 'disable']),
        protection_type=dict(type='str', required=False, choices=['cps', 'concurrent_connections'])
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'], log_level=log_level, logger=logger)
        
        if not module.check_mode:
            # Build the request body with only the parameters that were provided
            body = {}
            
            # Always include the protection name if provided
            if module.params['protection_name'] is not None:
                body["rsIDSConnectionLimitAttackName"] = module.params['protection_name']
            
            # Map and include user-friendly values if provided
            if module.params['protocol'] is not None:
                try:
                    body["rsIDSConnectionLimitAttackProtocol"] = PROTOCOL_MAP[module.params['protocol']]
                except KeyError:
                    module.fail_json(msg=f"Invalid protocol value: {module.params['protocol']}")
            
            if module.params['app_port_group'] is not None:
                body["rsIDSConnectionLimitAttackAppPort"] = module.params['app_port_group']
            
            if module.params['threshold'] is not None:
                body["rsIDSConnectionLimitAttackThreshold"] = module.params['threshold']
            
            if module.params['tracking_type'] is not None:
                try:
                    body["rsIDSConnectionLimitAttackTrackingType"] = TRACKING_TYPE_MAP[module.params['tracking_type']]
                except KeyError:
                    module.fail_json(msg=f"Invalid tracking_type value: {module.params['tracking_type']}")
            
            if module.params['action'] is not None:
                try:
                    body["rsIDSConnectionLimitAttackReportMode"] = ACTION_MAP[module.params['action']]
                except KeyError:
                    module.fail_json(msg=f"Invalid action value: {module.params['action']}")
            
            if module.params['packet_report'] is not None:
                try:
                    body["rsIDSConnectionLimitAttackPacketReport"] = PACKET_REPORT_MAP[module.params['packet_report']]
                except KeyError:
                    module.fail_json(msg=f"Invalid packet_report value: {module.params['packet_report']}")
            
            if module.params['protection_type'] is not None:
                try:
                    body["rsIDSConnectionLimitAttackType"] = ATTACK_TYPE_MAP[module.params['protection_type']]
                except KeyError:
                    module.fail_json(msg=f"Invalid protection_type value: {module.params['protection_type']}")
            
            # Only proceed if we have something to update
            if not body:
                module.exit_json(changed=False, msg="No parameters provided to update", **result)
            
            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsIDSConnectionLimitAttackTable/{module.params['protection_index']}"
            url = f"https://{provider['cc_ip']}{path}"
            debug_info = {
                'method': 'PUT',
                'url': url,
                'body': body
            }
            
            logger.info(f"Editing connection limit protection at index {module.params['protection_index']} on device {module.params['dp_ip']}")
            logger.debug(f"Request: {debug_info}")
            
            resp = cc._put(url, json=body)
            logger.debug(f"Response status: {resp.status_code}")
            
            try:
                data = resp.json()
                logger.debug(f"Response JSON: {data}")
            except ValueError:
                logger.error(f"Invalid JSON response: {resp.text}")
                raise Exception(f"Invalid JSON response: {resp.text}")
                
            result['response'] = data
            result['changed'] = True
            debug_info['response_status'] = resp.status_code
            debug_info['response_json'] = data
            
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)
        
    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
