# plugins/modules/get_bdos_profiles.py
"""
Ansible module to fetch one or more BDOS Flood profiles from Radware DefensePro devices via Radware CyberController API.

This module retrieves details of existing BDOS Flood profiles from one or multiple DefensePro devices.
Supports check mode, detailed logging, and multi-profile retrieval.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: get_bdos_profiles
short_description: Fetch one or more BDOS Flood profiles from DefensePro
description:
  - Retrieves one or more BDOS Flood profiles from DefensePro devices via Radware CC API.
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
    description: List of DefensePro device IP addresses
    type: list
    required: true
    elements: str
  profile_names:
    description: List of BDOS profile names to fetch
    type: list
    required: true
    elements: str
'''

EXAMPLES = r'''
- name: Fetch multiple BDOS Flood profiles
  get_bdos_profiles:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: radware
      log_level: debug
    dp_ip:
      - 10.105.192.32
      - 10.105.192.33
    profile_names:
      - BDOS_Profile_1
      - BDOS_Profile_2
'''

RETURN = r'''
response:
  description: API response per device and per profile
  type: dict
debug_info:
  description: Request and response debug info
  type: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='list', elements='str', required=True),
        profile_names=dict(type='list', elements='str', required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    dp_ips = module.params['dp_ip']
    profile_names = module.params['profile_names']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    result = dict(changed=False, response={}, debug_info={})

    # Handle check mode
    if module.check_mode:
        result['debug_info'] = {"info": "Check mode - no API calls made"}
        module.exit_json(**result)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        for dp_ip in dp_ips:
            result['response'][dp_ip] = {}
            for profile_name in profile_names:
                path = f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}"
                url = f"https://{provider['cc_ip']}{path}"
                result['debug_info'].setdefault('requests', []).append({'method': 'GET', 'url': url})

                logger.info(f"Fetching BDOS Flood profile '{profile_name}' from {dp_ip}")

                try:
                    resp = cc._get(url)
                    # Safe JSON decode
                    try:
                        data = resp.json()
                    except ValueError:
                        data = resp.text

                    result['debug_info'].setdefault('responses', []).append({
                        'dp_ip': dp_ip, 'profile': profile_name,
                        'status_code': resp.status_code, 'data': data
                    })

                    if resp.status_code in (200, 201):
                        result['response'][dp_ip][profile_name] = {'success': True, 'data': data}
                    else:
                        result['response'][dp_ip][profile_name] = {
                            'failed': True,
                            'status_code': resp.status_code,
                            'error': f"HTTP {resp.status_code}",
                            'data': data
                        }
                        logger.error(f"Failed to fetch profile '{profile_name}' from {dp_ip}: HTTP {resp.status_code}")

                except Exception as e:
                    result['response'][dp_ip][profile_name] = {'failed': True, 'error': str(e)}
                    logger.error(f"Error fetching profile '{profile_name}' from {dp_ip}: {e}")

    except Exception as e:
        module.fail_json(msg=f"Failed to fetch BDOS profiles: {str(e)}", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
