#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: get_http_profile
short_description: Retrieve an HTTPS Flood profile from Radware DefensePro
description:
  - Fetches the configuration of an HTTPS Flood profile on a DefensePro device via Radware CC API.
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
    description: Profile name to fetch
    type: str
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Get HTTPS Flood profile
  get_http_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.32
    name: "HTTPS_Profile_1"
'''

RETURN = r'''
response:
  description: API response containing the profile configuration
  type: dict
'''

def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            provider=dict(type='dict', required=True),
            dp_ip=dict(type='str', required=True),
            name=dict(type='str', required=True)
        ),
        supports_check_mode=True
    )

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    profile_name = module.params['name']
    result = {"changed": False, "response": {}}
    debug_info = {}

    logger = Logger(verbosity=provider.get('log_level', 'disabled'))

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=provider.get('log_level', 'disabled'), logger=logger)

        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsHttpsFloodProfileTable/{profile_name}"
        debug_info.update({"method": "GET", "url": url})

        if module.check_mode:
            module.exit_json(msg="Check mode: profile would be fetched", debug_info=debug_info)

        resp = cc._get(url)
        debug_info["response_status"] = resp.status_code

        if resp.status_code in [200]:
            if resp.headers.get("Content-Type") == "application/json":
                data = resp.json()
            else:
                data = {"raw": resp.text}
            result["response"] = data
        else:
            module.fail_json(msg=f"Failed to fetch profile: HTTP {resp.status_code}", debug_info=debug_info)

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result["debug_info"] = debug_info
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
