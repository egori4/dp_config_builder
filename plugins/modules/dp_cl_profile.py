# plugins/modules/dp_connection_limit_profile.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

DOCUMENTATION = r'''
---
module: dp_connection_limit_profile
short_description: Create or manage DefensePro IDS Connection Limit profiles
description:
  - Creates an IDS Connection Limit profile on Radware DefensePro via Radware CC API.
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
      - Dictionary of IDS Connection Limit profile attributes
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Create IDS Connection Limit profile
  dp_connection_limit_profile:
    provider:
      server: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    name: "Test_CL2"
    params:
      rsIDSConnectionLimitAttackProtocol: "3"
      rsIDSConnectionLimitAttackThreshold: "50"
      rsIDSConnectionLimitAttackTrackingType: "2"
      rsIDSConnectionLimitAttackReportMode: "10"
      rsIDSConnectionLimitAttackPacketReport: "2"
      rsIDSConnectionLimitAttackRisk: "3"
      rsIDSConnectionLimitAttackType: "1"
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
            # Always use numeric ID in the path (0)
            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsIDSConnectionLimitAttackTable/0/"
            body = {"rsIDSConnectionLimitAttackName": module.params['name']}
            body.update(module.params['params'])

            url = f"https://{provider['server']}{path}"
            debug_info = {
                'method': 'POST',
                'url': url,
                'body': body
            }
            logger.info(f"Creating IDS Connection Limit profile {module.params['name']} on device {module.params['dp_ip']}")
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
