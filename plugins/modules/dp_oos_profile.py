from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

DOCUMENTATION = r'''
---
module: dp_oos_profile
short_description: Create or manage DefensePro OOS (Stateful) profiles
description:
  - Creates an OOS / Stateful profile on Radware DefensePro via Radware CC API.
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
  name:
    type: str
    required: true
  params:
    description:
      - Dictionary of Stateful profile attributes (rsSTATFULProfile*)
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Create OOS Stateful profile
  dp_oos_profile:
    provider:
      server: 10.105.193.3
      username: radware
      password: radware
    dp_ip: 10.105.192.32
    name: "Test1"
    params:
      rsSTATFULProfileactThreshold: "5000"
      rsSTATFULProfiletermThreshold: "4000"
      rsSTATFULProfilesynAckAllow: "1"
      rsSTATFULProfilePacketTraceStatus: "1"
      rsSTATFULProfilePacketReportStatus: "1"
      rsSTATFULProfileRisk: "2"
      rsSTATFULProfileAction: "1"
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
        name=dict(type='str', required=True),
        params=dict(type='dict', required=True)
    )

    result = dict(changed=False, response={})
    debug_info = {}

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')

    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['server'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        if not module.check_mode:
            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsStatefulProfileTable/{module.params['name']}"
            body = {"rsSTATFULProfileName": module.params['name']}
            body.update(module.params['params'])

            url = f"https://{provider['server']}{path}"
            debug_info = {
                'method': 'POST',
                'url': url,
                'body': body
            }
            logger.info(f"Creating OOS Stateful profile {module.params['name']} on device {module.params['dp_ip']}")
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
