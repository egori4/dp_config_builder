"""
Ansible module to create Protected SSL Objects on Radware DefensePro via Radware CyberController API.

This module allows you to create a Protected SSL Object on Radware DefensePro devices
using the Radware CyberController API. It requires connection parameters for the CyberController,
the target DefensePro IP, and the SSL object details.

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
  ssl_object_name (str): Name of the Protected SSL Object.
  params (dict): Dictionary of SSL object parameters.
    - ssl_object_profile (str): Enable/disable state ("enable" or "disable").
    - IP_Address (str): Protected server IP address.
    - Port (int): Application port.

Returns:
  response (dict): API response from Radware CyberController.
  changed (bool): Indicates if any change was made.
  debug_info (dict): Debug information including request and response details.

References:
  - Radware CyberController API documentation for SSL object management.
  - AnsibleModule documentation: https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html
  - RadwareCC utility: ansible.module_utils.radware_cc
  - Logger utility: ansible.module_utils.logger
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: create_protected_ssl_object
short_description: Create Protected SSL Objects on DefensePro
description:
  - Creates a Protected SSL Object on Radware DefensePro via Radware CC API.
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
        description: Logging verbosity (info, debug, disabled)
        type: str
        required: false
        default: disabled
  dp_ip:
    description: Target DefensePro device IP address
    type: str
    required: true
  ssl_object_name:
    description: Name of the Protected SSL Object
    type: str
    required: true
  params:
    description:
      - Dictionary of SSL object parameters
    type: dict
    required: true
    suboptions:
      ssl_object_profile:
        description: Enable/disable state
        type: str
        choices: ["enable", "disable"]
      IP_Address:
        description: Protected server IP address
        type: str
      Port:
        description: Application port
        type: int
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Create Protected SSL Object
  create_protected_ssl_object:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    ssl_object_name: "server1"
    params:
      ssl_object_profile: "enable"
      IP_Address: "155.1.102.7"
      Port: 443
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
        ssl_object_name=dict(type='str', required=True),
        params=dict(type='dict', required=True)
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    # Map human-readable params to API fields
    body = {
        "rsProtectedObjName": module.params['ssl_object_name'],
        "rsProtectedObjEnable": "1" if module.params['params'].get('ssl_object_profile', 'enable') == "enable" else "2",
        "rsProtectedObjIpAddr": module.params['params'].get('IP_Address', ''),
        "rsProtectedObjApplPort": module.params['params'].get('Port', 443)
    }

    try:
        cc = RadwareCC(
            provider['cc_ip'],
            provider['username'],
            provider['password'],
            log_level=log_level,
            logger=logger
        )

        if not module.check_mode:
            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsProtectedSslObjTable/{module.params['ssl_object_name']}"
            url = f"https://{provider['cc_ip']}{path}"

            debug_info = {
                'method': 'POST',
                'url': url,
                'body': body
            }

            logger.info(f"Creating SSL Object {module.params['ssl_object_name']} on device {module.params['dp_ip']}")
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
