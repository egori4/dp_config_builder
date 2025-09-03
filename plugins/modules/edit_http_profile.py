#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: edit_http_profile
short_description: Edit an HTTP/HTTPS Flood profile on Radware DefensePro
description:
  - Edits an existing HTTP/HTTPS profile on a DefensePro device using PUT via Radware CC API.
options:
  provider:
    description: CC connection parameters
    type: dict
    required: true
    suboptions:
      cc_ip: {type: str, required: true}
      username: {type: str, required: true}
      password: {type: str, required: true}
  dp_ip:
    description: DefensePro device IP
    type: str
    required: true
  name:
    description: Profile name to edit (must exist on device)
    type: str
    required: true
  params:
    description: Dictionary of friendly parameters for the profile
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Edit HTTPS Flood profile (friendly parameters)
  edit_http_profile:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    name: "HTTPS_Demo1"
    params:
      Profile Action: "block & report"
      Rate Limit: "100"
      Selective Challenge: "disable"
      Collective Challenge: "enable"
      Challenge Method: "javaScript"
      Rate Limit Status: "enable"
      Full Session Decryption: "disable"
'''

RETURN = r'''
response:
  description: API response from CC
  type: dict
changed:
  description: True if the profile was updated
  type: bool
'''

# Friendly name → API key
PARAMS_MAP = {
    "Profile Action": "rsHttpsFloodProfileAction",
    "Rate Limit": "rsHttpsFloodProfileRateLimit",
    "Selective Challenge": "rsHttpsFloodProfileSelectiveChallenge",
    "Collective Challenge": "rsHttpsFloodProfileCollectiveChallenge",
    "Challenge Method": "rsHttpsFloodProfileChallengeMethod",
    "Rate Limit Status": "rsHttpsFloodProfileRateLimitStatus",
    "Full Session Decryption": "rsHttpsFloodProfileFullSessionDecryption",
}

# Friendly values → API numeric strings
NUMERIC_MAPPING = {
    "Profile Action": {"report": "0", "block & report": "1"},
    "Selective Challenge": {"enable": "1", "disable": "2"},
    "Collective Challenge": {"enable": "1", "disable": "2"},
    "Challenge Method": {"httpRedirect": "1", "javaScript": "2"},
    "Rate Limit Status": {"enable": "1", "disable": "2"},
    "Full Session Decryption": {"enable": "1", "disable": "2"},
}


def translate_params(params):
    """Convert friendly keys/values to API keys and string values."""
    translated = {}
    for k, v in params.items():
        api_key = PARAMS_MAP.get(k, k)
        if k in NUMERIC_MAPPING:
            translated[api_key] = NUMERIC_MAPPING[k].get(str(v), str(v))
        else:
            translated[api_key] = str(v)
    return translated


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            provider=dict(type='dict', required=True),
            dp_ip=dict(type='str', required=True),
            name=dict(type='str', required=True),
            params=dict(type='dict', required=True),
        ),
        supports_check_mode=True
    )

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    profile_name = module.params['name']
    params = translate_params(module.params['params'])

    result = {"changed": False, "response": {}}
    debug_info = {}

    logger = Logger(verbosity=provider.get('log_level', 'disabled'))

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=provider.get('log_level', 'disabled'), logger=logger)

        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsHttpsFloodProfileTable/{profile_name}"
        debug_info.update({"method": "PUT", "url": url, "body": params})

        if module.check_mode:
            module.exit_json(changed=True, msg="Check mode: profile would be edited", debug_info=debug_info)

        resp = cc._put(url, json=params)
        debug_info["response_status"] = resp.status_code

        if resp.headers.get("Content-Type") == "application/json":
            data = resp.json()
        else:
            data = {"raw": resp.text}

        if resp.status_code in [200, 204]:
            result["changed"] = True
        else:
            module.fail_json(msg=f"Failed to edit profile: HTTP {resp.status_code}", debug_info=debug_info)

        result["response"] = data
        debug_info["response_json"] = data

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result["debug_info"] = debug_info
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
