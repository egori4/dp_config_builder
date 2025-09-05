# plugins/modules/edit_network_class.py
"""
Ansible module to edit existing DefensePro network class groups via Radware CyberController API.

This module allows you to modify an existing network class group on Radware DefensePro devices
using the Radware CyberController API. It requires connection parameters for the Radware CyberController, 
the target DefensePro IP, and network class details to modify.

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
  class_name (str): Name of the existing network class to modify.
  address (str): New network address for the class group.
  mask (str): New network mask for the class group.
  index (int): Sub-index of the network group to modify.

Returns:
  response (dict): API response from Radware CyberController.
  changed (bool): Indicates if any change was made.
  debug_info (dict): Debug information including request and response details.

Exceptions:
  Raises Exception if API response is invalid or if any error occurs during execution.

References:
  - Radware CyberController API documentation for network class management.
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
module: edit_network_class
short_description: Edit existing DefensePro network class groups
description:
  - Modifies an existing network class group on Radware DefensePro via Radware CC API.
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
  class_name:
    type: str
    required: true
  address:
    type: str
    required: true
  mask:
    type: str
    required: true
  index:
    type: int
    required: true
'''

EXAMPLES = r'''
- name: Edit a network class group
  edit_network_class:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.32
    class_name: egor_test_net
    address: 155.1.117.0
    mask: 27
    index: 2
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
    class_name=dict(type='str', required=True),
    address=dict(type='str', required=True),
    mask=dict(type='str', required=True),
    index=dict(type='int', required=True)
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
      path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsBWMNetworkTable/{module.params['class_name']}/{module.params['index']}"
      body = {
        "rsBWMNetworkName": module.params['class_name'],
        "rsBWMNetworkAddress": module.params['address'],
        "rsBWMNetworkMask": module.params['mask']
      }
      url = f"https://{provider['cc_ip']}{path}"
      debug_info = {
        'method': 'PUT',
        'url': url,
        'body': body
      }
      logger.info(f"Editing network class {module.params['class_name']} at index {module.params['index']} on device {module.params['dp_ip']}")
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
