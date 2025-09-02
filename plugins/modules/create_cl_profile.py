# plugins/modules/create_cl_profile.py
"""
Ansible module to create or manage DefensePro connection limit profiles and attach protections via Radware CyberController API.

This module allows you to create connection limit profiles and attach connection limit protection subprofiles
on Radware DefensePro devices using the Radware CyberController API. It requires connection parameters for the 
Radware CyberController, the target DefensePro IP, and profile details.

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
  profile_name (str): Name of the connection limit profile to create.
  protection_name (str): Name of the connection limit protection to attach.

Returns:
  response (dict): API response from Radware CyberController.
  changed (bool): Indicates if any change was made.
  debug_info (dict): Debug information including request and response details.

Exceptions:
  Raises Exception if API response is invalid or if any error occurs during execution.

References:
  - Radware CyberController API documentation for connection limit profile management.
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
module: create_cl_profile
short_description: Create or manage DefensePro connection limit profiles
description:
  - Creates connection limit profiles and attaches protection subprofiles on Radware DefensePro via Radware CC API.
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
  profile_name:
    type: str
    required: true
  protection_name:
    type: str
    required: true
'''

EXAMPLES = r'''
- name: Create a connection limit profile and attach protection
  create_cl_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.32
    profile_name: cl_prof_egor_test10
    protection_name: cl_prot_egor_test10
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
        profile_name=dict(type='str', required=True),
        protection_name=dict(type='str', required=True)
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
            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsIDSConnectionLimitProfileTable/{module.params['profile_name']}/{module.params['protection_name']}"
            body = {
                "rsIDSConnectionLimitProfileName": module.params['profile_name'],
                "rsIDSConnectionLimitProfileAttackName": module.params['protection_name']
            }
            
            url = f"https://{provider['cc_ip']}{path}"
            debug_info = {
                'method': 'POST',
                'url': url,
                'body': body
            }
            
            logger.info(f"Creating connection limit profile {module.params['profile_name']} with protection {module.params['protection_name']} on device {module.params['dp_ip']}")
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
