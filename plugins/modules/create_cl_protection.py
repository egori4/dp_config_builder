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
    type: str
    default: '3'
  threshold:
    type: str
    default: '50'
  tracking_type:
    type: str
    default: '2'
  report_mode:
    type: str
    default: '10'
  packet_report:
    type: str
    default: '2'
  risk:
    type: str
    default: '3'
  attack_type:
    type: str
    default: '1'
  index:
    type: int
    default: 0
'''

EXAMPLES = r'''
- name: Create a connection limit protection
  create_cl_protection:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.32
    protection_name: cl_prot_egor_test10
    protocol: '3'
    threshold: '50'
    tracking_type: '2'
    report_mode: '10'
    packet_report: '2'
    risk: '3'
    attack_type: '1'
    index: 0
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        protection_name=dict(type='str', required=True),
        protocol=dict(type='str', required=False, default='3'),
        threshold=dict(type='str', required=False, default='50'),
        tracking_type=dict(type='str', required=False, default='2'),
        report_mode=dict(type='str', required=False, default='10'),
        packet_report=dict(type='str', required=False, default='2'),
        risk=dict(type='str', required=False, default='3'),
        attack_type=dict(type='str', required=False, default='1'),
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
                "rsIDSConnectionLimitAttackProtocol": module.params['protocol'],
                "rsIDSConnectionLimitAttackThreshold": module.params['threshold'],
                "rsIDSConnectionLimitAttackTrackingType": module.params['tracking_type'],
                "rsIDSConnectionLimitAttackReportMode": module.params['report_mode'],
                "rsIDSConnectionLimitAttackPacketReport": module.params['packet_report'],
                "rsIDSConnectionLimitAttackRisk": module.params['risk'],
                "rsIDSConnectionLimitAttackType": module.params['attack_type']
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
