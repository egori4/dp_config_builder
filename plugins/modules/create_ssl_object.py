from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

DOCUMENTATION = r'''
---
module: create_protected_ssl_object
short_description: Create or manage Protected SSL Objects on DefensePro
description:
  - Creates a Protected SSL Object on Radware DefensePro via Radware CC API.
options:
  provider:
    description:
      - Dictionary with CC connection parameters
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
    description: DefensePro device IP
    type: str
    required: true
  ssl_object_name:
    description: Name of the Protected SSL Object
    type: str
    required: true
  params:
    description:
      - Dictionary of human-readable SSL object attributes
        - ssl_object_profile: enable/disable
        - IP_Address: object IP
        - Port: application port
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Create Protected SSL Object
  create_protected_ssl_object:
    provider:
      server: 155.1.1.6
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

    # Map human-readable params to API fields
    body = {
        "rsProtectedObjName": module.params['ssl_object_name'],
        "rsProtectedObjEnable": "1" if module.params['params'].get('ssl_object_profile','enable') == "enable" else "2",
        "rsProtectedObjIpAddr": module.params['params'].get('IP_Address', ''),
        "rsProtectedObjApplPort": module.params['params'].get('Port', 443)
    }

    from ansible.module_utils.logger import Logger
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['server'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        if not module.check_mode:
            url = f"https://{provider['server']}/mgmt/device/byip/{module.params['dp_ip']}/config/rsProtectedSslObjTable/{module.params['ssl_object_name']}"
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
