# plugins/modules/dp_network_class.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

DOCUMENTATION = r'''
---
module: dp_network_class
short_description: Create or manage DefensePro network classes
description:
  - Creates a network class and adds network groups on Radware DefensePro via Radware CC API.
options:
  provider:
    description:
      - Dictionary with connection parameters.
    type: dict
    required: true
    suboptions:
      server:
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
    default: 0
'''

EXAMPLES = r'''
- name: Create a network class
  dp_network_class:
    provider:
      server: 10.105.193.3
      username: radware
      password: mypass
    device_ip: 10.105.192.32
    class_name: my_network_class
    address: 192.168.1.0
    mask: 255.255.255.0
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
    class_name=dict(type='str', required=True),
    address=dict(type='str', required=True),
    mask=dict(type='str', required=True),
    index=dict(type='int', required=False, default=0)
  )

  result = dict(changed=False, response={})
  debug_info = {}
  module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
  provider = module.params['provider']
  log_level = provider.get('log_level', 'disabled')
  from ansible.module_utils.logger import Logger
  logger = Logger(verbosity=log_level)

  try:
    cc = RadwareCC(provider['server'], provider['username'], provider['password'], log_level=log_level, logger=logger)
    if not module.check_mode:
      path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsBWMNetworkTable/{module.params['class_name']}/{module.params['index']}"
      body = {
        "rsBWMNetworkName": module.params['class_name'],
        "rsBWMNetworkSubIndex": module.params['index'],
        "rsBWMNetworkAddress": module.params['address'],
        "rsBWMNetworkMask": module.params['mask'],
        "rsBWMNetworkMode": "1"
      }
      url = f"https://{provider['server']}{path}"
      debug_info = {
        'method': 'POST',
        'url': url,
        'body': body
      }
      logger.info(f"Creating network class {module.params['class_name']} at index {module.params['index']} on device {module.params['dp_ip']}")
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
