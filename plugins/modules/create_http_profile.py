#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

DOCUMENTATION = r'''
---
module: dp_https_profile
short_description: Manage DefensePro HTTPS Flood profiles
description:
  - Creates or updates an HTTPS Flood profile on Radware DefensePro via Radware CC API.
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
    description:
      - DefensePro device IP managed by CC
    type: str
    required: true
  name:
    description:
      - HTTPS Flood profile name
    type: str
    required: true
  params:
    description:
      - Dictionary of HTTPS Flood profile attributes (friendly keys mapped to rsHttpsFloodProfile* API fields)
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Create HTTPS Flood profile
  dp_https_profile:
    provider:
      server: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    name: "HTTPS_Demo1"
    params:
      Https_Flood_Profile_Action: "1"
      Https_Flood_Profile_RateLimit: "100"
      Https_Flood_Profile_Selective_Challenge: "2"
      Https_Flood_Profile_Collective_Challenge: "2"
      Https_Flood_Profile_Challenge_Method: "2"
      Https_Flood_Profile_RateLimit_Status: "1"
      Https_Flood_Profile_FullSession_Decryption: "2"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
'''

# Mapping between friendly names (playbook) and CC API fields
PARAMS_MAP = {
    "Https_Flood_Profile_Action": "rsHttpsFloodProfileAction",
    "Https_Flood_Profile_RateLimit": "rsHttpsFloodProfileRateLimit",
    "Https_Flood_Profile_Selective_Challenge": "rsHttpsFloodProfileSelectiveChallenge",
    "Https_Flood_Profile_Collective_Challenge": "rsHttpsFloodProfileCollectiveChallenge",
    "Https_Flood_Profile_Challenge_Method": "rsHttpsFloodProfileChallengeMethod",
    "Https_Flood_Profile_RateLimit_Status": "rsHttpsFloodProfileRateLimitStatus",
    "Https_Flood_Profile_FullSession_Decryption": "rsHttpsFloodProfileFullSessionDecryption",
}

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
            # Build API body with mapped keys
            body = {"rsHttpsFloodProfileName": module.params['name']}
            for friendly, api_field in PARAMS_MAP.items():
                if friendly in module.params['params']:
                    body[api_field] = module.params['params'][friendly]

            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsHttpsFloodProfileTable/{module.params['name']}"
            url = f"https://{provider['server']}{path}"

            debug_info = {
                'method': 'POST',
                'url': url,
                'body': body
            }
            logger.info(f"Creating/Updating HTTPS Flood profile {module.params['name']} on {module.params['dp_ip']}")
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
