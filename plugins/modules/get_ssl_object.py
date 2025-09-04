"""
Ansible module to retrieve Protected SSL Objects on Radware DefensePro via Radware CyberController API.

This module allows you to fetch details of a Protected SSL Object (or all SSL objects)
from Radware DefensePro devices using the Radware CyberController API. It requires
connection parameters for the CyberController and the target DefensePro IP.

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
  ssl_object_name (str, optional): Name of the Protected SSL Object to retrieve.
                                   If not provided, all SSL objects will be fetched.

Returns:
  response (dict): API response from Radware CyberController.
  changed (bool): Always false, since this is a read-only operation.
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
module: get_protected_ssl_object
short_description: Retrieve Protected SSL Objects on DefensePro
description:
  - Retrieves details of Protected SSL Objects on Radware DefensePro via Radware CC API.
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
    description: Name of the Protected SSL Object to retrieve (optional).
                 If omitted, retrieves all SSL objects.
    type: str
    required: false
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Get all SSL Objects from device
  get_protected_ssl_object:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.32

- name: Get specific SSL Object from device
  get_protected_ssl_object:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.32
    ssl_object_name: "server1"
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
        ssl_object_name=dict(type='str', required=False, default=None)
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(
            provider['cc_ip'],
            provider['username'],
            provider['password'],
            log_level=log_level,
            logger=logger
        )

        if not module.check_mode:
            base_path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsProtectedSslObjTable"
            if module.params['ssl_object_name']:
                path = f"{base_path}/{module.params['ssl_object_name']}"
            else:
                path = base_path

            url = f"https://{provider['cc_ip']}{path}"
            debug_info = {
                'method': 'GET',
                'url': url
            }

            logger.info(f"Fetching SSL Object(s) from device {module.params['dp_ip']}")
            logger.debug(f"Request: {debug_info}")

            resp = cc._get(url)
            logger.debug(f"Response status: {resp.status_code}")

            try:
                data = resp.json()
                logger.debug(f"Response JSON: {data}")
            except ValueError:
                data = {}
                logger.warning(f"Response is not JSON: {resp.text}")

            result['response'] = data
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
