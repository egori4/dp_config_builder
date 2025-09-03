#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: get_bdos_profile
short_description: Retrieve a BDOS Flood profile from DefensePro
description:
  - Fetches BDOS Flood profile configuration from Radware DefensePro using Radware CC API.
options:
  provider:
    description: Dictionary with connection parameters for Radware CC.
    type: dict
    required: true
    suboptions:
      cc_ip:
        description: Radware CC IP address
        type: str
        required: true
      username:
        description: Radware CC username
        type: str
        required: true
      password:
        description: Radware CC password
        type: str
        required: true
      log_level:
        description: Logging verbosity (disabled, info, debug)
        type: str
        default: disabled
  dp_ip:
    description: DefensePro device IP address
    type: str
    required: true
  profile_name:
    description: BDOS Flood profile name
    type: str
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Get BDOS Flood profile
  get_bdos_profile:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
      log_level: debug
    dp_ip: 155.1.1.7
    profile_name: "BDOS_Test"
'''

RETURN = r'''
response:
  description: API response containing the BDOS Flood profile configuration
  type: dict
debug_info:
  description: Request/response debug details
  type: dict
'''

# -------------------------------
# Helpers
# -------------------------------
def build_api_path(dp_ip, profile_name):
    return f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}"

# -------------------------------
# Main Module Logic
# -------------------------------
def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        profile_name=dict(type='str', required=True),
    )

    result = dict(changed=False, response={}, debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    profile_name = module.params['profile_name']
    log_level = provider.get('log_level', 'disabled')

    logger = Logger(verbosity=log_level)
    debug_info = {}

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        path = build_api_path(dp_ip, profile_name)
        url = f"https://{provider['cc_ip']}{path}"

        debug_info['request'] = {"method": "GET", "url": url}
        logger.info(f"Fetching BDOS Flood profile '{profile_name}' from {dp_ip}")

        if module.check_mode:
            result['response'] = {"msg": "Check mode - no changes applied"}
        else:
            resp = cc.get(url)
            debug_info['response_status'] = resp.status_code
            try:
                data = resp.json()
                debug_info['response_json'] = data
            except ValueError:
                raise Exception(f"Invalid JSON response: {resp.text}")

            if resp.status_code != 200:
                raise Exception(f"Failed to fetch BDOS profile: {data}")

            result['response'] = data

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == "__main__":
    main()
