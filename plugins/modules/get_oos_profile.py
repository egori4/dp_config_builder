# plugins/modules/get_oos_profile.py
"""
Ansible module to fetch specific OOS (Stateful) profiles from Radware DefensePro via CyberController API.

Supports fetching one or multiple profile names and returns results in loop-friendly format
with debug_info, response, changed, failed, and invocation details.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: get_oos_profile
short_description: Retrieve specific OOS Stateful profiles from DefensePro
description:
  - Fetches specific Stateful (OOS) profiles from a specified DefensePro device using Radware CyberController API.
options:
  provider:
    description:
      - Dictionary with connection parameters.
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
        description: Logging verbosity
        type: str
        default: "disabled"
  dp_ip:
    description:
      - Target DefensePro device IP address
    type: str
    required: true
  name:
    description:
      - Specific OOS profile name to fetch
    type: str
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Get specific OOS profile
  get_oos_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
      log_level: debug
    dp_ip: 10.105.192.32
    name: "OOS_Profile_1"
'''

RETURN = r'''
results:
  description: List of looped results for each device/profile
  type: list
  elements: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=True)
    )

    result = dict(changed=False, results=[])
    debug_info = {}

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    profile_name = module.params['name']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'], log_level=log_level, logger=logger)
        path = f"/mgmt/device/byip/{dp_ip}/config/rsStatefulProfileTable/{profile_name}"
        url = f"https://{provider['cc_ip']}{path}"
        debug_info = {'method': 'GET', 'url': url}

        logger.info(f"Fetching OOS Stateful profile '{profile_name}' from device {dp_ip}")
        resp = cc._get(url)
        debug_info["response_status"] = resp.status_code

        if resp.status_code != 200:
            payload = resp.text
            try:
                payload = resp.json()
            except Exception:
                pass
            debug_info["response_error"] = payload
            raise Exception(f"API error {resp.status_code}: {payload}")

        try:
            data = resp.json()
        except ValueError:
            raise Exception(f"Invalid JSON response: {resp.text}")

        # Prepare loop-friendly result
        result_item = {
            'item': dp_ip,
            'changed': False,
            'failed': False,
            'response': data,
            'debug_info': debug_info,
            'invocation': {
                'module_args': module.params
            }
        }

        result['results'].append(result_item)

    except Exception as e:
        logger.error(f"Exception: {e}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
