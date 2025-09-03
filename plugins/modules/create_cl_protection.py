# plugins/modules/create_cl_protection.py
"""
Ansible module to create or manage DefensePro connection limit protection subprofiles via Radware CyberController API.

This module allows you to create connection limit protection subprofiles on Radware DefensePro devices
using the Radware CyberController API. It requires connection parameters for the Radware CyberController, the target DefensePro IP,
and connection limit protection details.

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
  protection_name (str): Name of the connection limit protection to create.
  protocol (str, optional): Protocol type (default: '3').
  threshold (str, optional): Connection limit threshold (default: '50').
  tracking_type (str, optional): Tracking type (default: '2').
  report_mode (str, optional): Report mode (default: '10').
  packet_report (str, optional): Packet report (default: '2').
  risk (str, optional): Risk level (default: '3').
  attack_type (str, optional): Attack type (default: '1').
  index (int, optional): Index for the protection (default: 0).

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
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: create_cl_protection
short_description: Create or manage DefensePro connection limit protection subprofiles
description:
  - Creates connection limit protection subprofiles on Radware DefensePro via Radware CC API.
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
  protection_name:
    type: str
    required: true
  protocol:
    description:
      - Protocol type for connection limit protection
    type: str
    choices: ['tcp', 'udp']
    default: 'tcp'
  threshold:
    description:
      - Connection limit threshold (number of connections)
    type: str
    default: '50'
  tracking_type:
    description:
      - Type of connection counting for connection limiting
    type: str
    choices: ['src_ip', 'dst_ip', 'src_and_dest_ip', 'dst_ip_and_port']
    default: 'dst_ip'
  action:
    description:
      - Action to take when connection limit is exceeded
    type: str
    choices: ['report_only', 'drop']
    default: 'drop'
  packet_report:
    description:
      - Per-attack packet report setting
    type: str
    choices: ['enable', 'disable'] 
    default: 'disable'
  protection_type:
    description:
      - Type of connection limit protection detection
    type: str  
    choices: ['cps', 'concurrent_connections']
    default: 'cps'
  index:
    type: int
    default: 0
'''

EXAMPLES = r'''
# Example of how the module is called within a playbook task
# Variables come from vars/create_vars.yml file
- name: "Create connection limit protection {{ item.1.name }} on {{ item.0 }}"
  create_cl_protection:
    provider: "{{ cc }}"
    dp_ip: "{{ item.0 }}"
    protection_name: "{{ item.1.name }}"
    protocol: "{{ item.1.protocol | default('tcp') }}"
    threshold: "{{ item.1.threshold | default('50') }}"
    tracking_type: "{{ item.1.tracking_type | default('dst_ip') }}"
    action: "{{ item.1.action | default('drop') }}"
    packet_report: "{{ item.1.packet_report | default('disable') }}"
    protection_type: "{{ item.1.protection_type | default('cps') }}"
    index: 0
    refresh_state: "{{ not ansible_loop.first }}"

# Direct module call example (for testing or standalone use)
- name: Create a specific connection limit protection
  create_cl_protection:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.32
    protection_name: tcp_conn_limit
    protocol: 'tcp'
    threshold: '100'
    tracking_type: 'src_ip'
    action: 'drop'
    packet_report: 'enable'
    protection_type: 'concurrent_connections'
    index: 0
'''

RETURN = r'''
response:
  description: API response from Radware CC
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
        protection_name=dict(type='str', required=True),
        protocol=dict(type='str', required=False, default='tcp', 
                     choices=['tcp', 'udp']),
        threshold=dict(type='str', required=False, default='50'),
        tracking_type=dict(type='str', required=False, default='dst_ip',
                          choices=['src_ip', 'dst_ip', 'src_and_dest_ip', 'dst_ip_and_port']),
        action=dict(type='str', required=False, default='drop',
                   choices=['report_only', 'drop']),
        packet_report=dict(type='str', required=False, default='disable',
                          choices=['enable', 'disable']),
        protection_type=dict(type='str', required=False, default='cps',
                        choices=['cps', 'concurrent_connections']),
        index=dict(type='int', required=False, default=0),
        refresh_state=dict(type='bool', required=False, default=False)
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'], log_level=log_level, logger=logger)
        
        # Validate and convert user-friendly values to API values
        try:
            api_protocol = PROTOCOL_MAP[module.params['protocol']]
            api_tracking_type = TRACKING_TYPE_MAP[module.params['tracking_type']]  
            api_protection_type = ATTACK_TYPE_MAP[module.params['protection_type']]
            api_action = ACTION_MAP[module.params['action']]
            api_packet_report = PACKET_REPORT_MAP[module.params['packet_report']]
        except KeyError as e:
            module.fail_json(msg=f"Invalid parameter value: {e}")
        
        if not module.check_mode:
            # Refresh device state if requested (helps avoid API caching issues)
            if module.params['refresh_state']:
                logger.info("Refreshing device state by reading current protection table")
                refresh_url = f"https://{provider['cc_ip']}/mgmt/device/byip/{module.params['dp_ip']}/config/rsIDSConnectionLimitAttackTable"
                try:
                    refresh_resp = cc._get(refresh_url)
                    logger.debug(f"State refresh response: {refresh_resp.status_code}")
                except Exception as e:
                    logger.warning(f"State refresh failed (continuing anyway): {str(e)}")
            
            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsIDSConnectionLimitAttackTable/{module.params['index']}"
            body = {
                "rsIDSConnectionLimitAttackName": module.params['protection_name'],
                "rsIDSConnectionLimitAttackProtocol": api_protocol,
                "rsIDSConnectionLimitAttackThreshold": module.params['threshold'],
                "rsIDSConnectionLimitAttackTrackingType": api_tracking_type,
                "rsIDSConnectionLimitAttackReportMode": api_action,
                "rsIDSConnectionLimitAttackPacketReport": api_packet_report,
                "rsIDSConnectionLimitAttackType": api_protection_type
            }
            
            url = f"https://{provider['cc_ip']}{path}"
            debug_info = {
                'method': 'POST',
                'url': url,
                'body': body
            }
            
            logger.info(f"Creating connection limit protection {module.params['protection_name']} at index {module.params['index']} on device {module.params['dp_ip']}")
            logger.debug(f"Request: {debug_info}")
            
            resp = cc._post(url, json=body)
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
