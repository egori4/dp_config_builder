# plugins/modules/delete_dns_profile.py
"""
Ansible module to delete a DNS Protection profile from DefensePro via Radware CyberController API.

This module allows you to delete a DNS Protection profile on Radware DefensePro devices
using the Radware CyberController API. It requires connection parameters for the Radware CyberController,
the target DefensePro IP, and the profile name.

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
  name (str): DNS profile name to delete.

Returns:
  response (dict): API response from Radware CyberController.
  changed (bool): Indicates if any change was made.
  debug_info (dict): Debug information including request and response details.
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: delete_dns_profile
short_description: Delete a DNS Protection profile from DefensePro
options:
  provider:
    description:
      - Dictionary with connection parameters.
    type: dict
    required: true
    suboptions:
      cc_ip:
        description: CyberController IP address
        type: str
        required: true
      username:
        description: Username for authentication
        type: str
        required: true
      password:
        description: Password for authentication
        type: str
        required: true
      log_level:
        description: Logging verbosity
        type: str
        required: false
        default: "disabled"
  dp_ip:
    description: Target DefensePro device IP
    type: str
    required: true
  name:
    description: DNS profile name to delete
    type: str
    required: true
'''

EXAMPLES = r'''
- name: Delete DNS Protection profile
  delete_dns_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.33
    name: "DNS_Profile_1"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
debug_info:
  description: Internal debug information including request and response
  type: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=True)
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    profile_name = module.params['name']
    log_level = provider.get('log_level', 'disabled')

    result = dict(changed=False, response={}, debug_info={})
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(
            provider['cc_ip'],
            provider['username'],
            provider['password'],
            log_level=log_level,
            logger=logger
        )

        if module.check_mode:
            module.exit_json(**result)

        path = f"/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}"
        url = f"https://{provider['cc_ip']}{path}"

        result['debug_info'] = {'method': 'DELETE', 'url': url, 'body': None}

        logger.info(f"Deleting DNS Protection profile '{profile_name}' on device {dp_ip}")
        logger.debug(f"Request info: {result['debug_info']}")

        resp = cc._delete(url)
        logger.debug(f"Response status: {resp.status_code}")

        try:
            data = resp.json()
        except ValueError:
            logger.error(f"Invalid JSON response: {resp.text}")
            raise Exception(f"Invalid JSON response: {resp.text}")

        result['response'] = data
        result['changed'] = True
        result['debug_info'].update({'response_status': resp.status_code, 'response_json': data})

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
