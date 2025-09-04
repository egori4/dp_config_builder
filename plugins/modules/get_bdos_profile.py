# plugins/modules/get_bdos_profile.py
"""
Ansible module to fetch BDOS Flood profiles from Radware DefensePro devices via Radware CyberController API.

This module retrieves details of an existing BDOS Flood profile on a DefensePro device using
the Radware CC API. Supports check mode and detailed logging.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: get_bdos_profile
short_description: Fetch BDOS Flood profiles from DefensePro
description:
  - Retrieves a BDOS Flood profile from a DefensePro device via Radware CC API.
options:
  provider:
    description:
      - Dictionary with Radware CC connection details.
    type: dict
    required: true
    suboptions:
      cc_ip:
        description: CC IP address
        type: str
        required: true
      username:
        description: CC username
        type: str
        required: true
      password:
        description: CC password
        type: str
        required: true
      log_level:
        description: Log verbosity level
        type: str
        default: disabled
  dp_ip:
    description: DefensePro device IP address
    type: str
    required: true
  name:
    description: Name of the BDOS Flood profile to fetch
    type: str
    required: true
'''

EXAMPLES = r'''
- name: Get BDOS Flood profile
  get_bdos_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: radware
      log_level: debug
    dp_ip: 10.105.192.32
    name: BDOS_Profile_10
'''

RETURN = r'''
response:
  description: API response containing BDOS Flood profile details
  type: dict
debug_info:
  description: Request/response debug info
  type: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=True),
    )

    result = dict(changed=False, response={}, debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    name = module.params['name']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    debug_info = {}

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        path = f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{name}"
        url = f"https://{provider['cc_ip']}{path}"
        debug_info['request'] = {'method': 'GET', 'url': url}

        logger.info(f"Fetching BDOS Flood profile '{name}' from {dp_ip}")
        resp = cc._get(url)
        debug_info['response_status'] = resp.status_code

        try:
            data = resp.json()
            debug_info['response_json'] = data
        except ValueError:
            raise Exception(f"Invalid JSON response: {resp.text}")

        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to fetch BDOS profile '{name}': {data}")

        result['response'] = data

    except Exception as e:
        result['debug_info'] = debug_info
        module.fail_json(msg=str(e), **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == "__main__":
    main()
