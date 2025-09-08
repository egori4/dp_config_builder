#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: create_dp_profile
short_description: Manage DefensePro SSL and HTTPS Flood profiles
description:
  - Creates or updates Protected SSL Objects or HTTPS Flood profiles on Radware DefensePro via Radware CC API.
options:
  profile_type:
    description:
      - Type of profile to manage: "ssl" for Protected SSL Object, "https" for HTTPS Flood profile
    type: str
    required: true
    choices: ["ssl", "https"]
  provider:
    description:
      - Dictionary with connection parameters for CyberController
    type: dict
    required: true
    suboptions:
      cc_ip:
        description: CyberController IP address
        type: str
        required: true
      username:
        type: str
        required: true
      password:
        type: str
        required: true
      log_level:
        type: str
        required: false
        default: disabled
  dp_ip:
    description:
      - Target DefensePro device IP
    type: str
    required: true
  name:
    description:
      - Profile name (SSL Object name or HTTPS Flood profile name)
    type: str
    required: true
  params:
    description:
      - Dictionary of profile parameters
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
# Create SSL Object
- name: Create SSL Object
  create_dp_profile:
    profile_type: ssl
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    name: "server1"
    params:
      ssl_object_profile: "enable"
      IP_Address: "155.1.102.7"
      Port: 443

# Create HTTPS Flood profile
- name: Create HTTPS Flood profile
  create_dp_profile:
    profile_type: https
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    name: "HTTPS_Demo1"
    params:
      Profile Action: "block-and-report"
      Rate Limit: "100000"
      Selective Challenge: "enable"
      Collective Challenge: "enable"
      Challenge Method: "httpRedirect"
      Rate Limit Status: "disable"
      Full Session Decryption: "disable"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
'''

# HTTPS Flood profile mappings
HTTPS_PARAMS_MAP = {
    "Profile Action": "rsHttpsFloodProfileAction",
    "Rate Limit": "rsHttpsFloodProfileRateLimit",
    "Selective Challenge": "rsHttpsFloodProfileSelectiveChallenge",
    "Collective Challenge": "rsHttpsFloodProfileCollectiveChallenge",
    "Challenge Method": "rsHttpsFloodProfileChallengeMethod",
    "Rate Limit Status": "rsHttpsFloodProfileRateLimitStatus",
    "Full Session Decryption": "rsHttpsFloodProfileFullSessionDecryption",
}

HTTPS_NUMERIC_MAPPING = {
    "Profile Action": {"report": 0, "block & report": 1},
    "Selective Challenge": {"enable": 1, "disable": 2},
    "Collective Challenge": {"enable": 1, "disable": 2},
    "Challenge Method": {"httpRedirect": 1, "javaScript": 2},
    "Rate Limit Status": {"enable": 1, "disable": 2},
    "Full Session Decryption": {"enable": 1, "disable": 2},
}

def translate_https_params(params):
    translated = {}
    for k, v in params.items():
        api_key = HTTPS_PARAMS_MAP.get(k, k)
        if k in HTTPS_NUMERIC_MAPPING:
            translated[api_key] = HTTPS_NUMERIC_MAPPING[k].get(str(v), v)
        else:
            translated[api_key] = int(v) if str(v).isdigit() else v
    return translated

def run_module():
    module_args = dict(
        profile_type=dict(type='str', required=True, choices=['ssl', 'https']),
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
    logger = Logger(verbosity=log_level)
    profile_type = module.params['profile_type']

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        if not module.check_mode:
            if profile_type == "ssl":
                # SSL Object body
                body = {
                    "rsProtectedObjName": module.params['name'],
                    "rsProtectedObjEnable": "1" if module.params['params'].get('ssl_object_profile', 'enable')=="enable" else "2",
                    "rsProtectedObjIpAddr": module.params['params'].get('IP_Address', ''),
                    "rsProtectedObjApplPort": module.params['params'].get('Port', 443)
                }
                path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsProtectedSslObjTable/{module.params['name']}"

            else:
                # HTTPS Flood profile body
                body = {"rsHttpsFloodProfileName": module.params['name']}
                body.update(translate_https_params(module.params['params']))
                path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsHttpsFloodProfileTable/{module.params['name']}"

            url = f"https://{provider['cc_ip']}{path}"
            debug_info.update({"method": "POST", "url": url, "body": body})
            logger.info(f"Creating/Updating {profile_type.upper()} profile {module.params['name']} on {module.params['dp_ip']}")
            logger.debug(f"Request: {debug_info}")

            resp = cc._post(url, json=body)
            debug_info["response_status"] = resp.status_code

            try:
                data = resp.json()
            except ValueError:
                data = {"raw": resp.text}

            result.update({"response": data, "changed": True})
            debug_info["response_json"] = data

    except Exception as e:
        logger.error(f"Exception: {e}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result["debug_info"] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == "__main__":
    main()
