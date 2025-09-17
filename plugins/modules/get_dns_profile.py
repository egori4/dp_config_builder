# plugins/modules/get_dns_profile.py
"""
Ansible module to fetch DNS Protection profiles from DefensePro devices .

Features:
- Retrieve one DNS profile at a time.
- Handles missing profiles gracefully.
- Returns structured results per profile for easy parsing in Ansible.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: get_dns_profile
short_description: Fetch DNS Protection profiles from DefensePro
description:
  - Retrieves a DNS Protection profile from Radware DefensePro via Radware CC API.
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
  dp_ip:
    type: str
    required: true
  name:
    type: str
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Get a DNS Protection profile
  get_dns_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.32
    name: "DNS_Profile_1"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
profile_exists:
  description: Indicates if the requested profile exists on the device
  type: bool
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=True)
    )

    result = dict(changed=False, response={}, profile_exists=False)
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsDnsProtProfileTable/{module.params['name']}"
        url = f"https://{provider['cc_ip']}{path}"

        debug_info = {
            'method': 'GET',
            'url': url,
            'body': None
        }
        logger.info(f"Fetching DNS Protection profile '{module.params['name']}' from device {module.params['dp_ip']}")
        logger.debug(f"Request: {debug_info}")

        resp = cc._get(url)
        logger.debug(f"Response status: {resp.status_code}")

        try:
            data = resp.json()
            logger.debug(f"Response JSON: {data}")
            if isinstance(data, dict) and data.get('status') == 'error':
                result['profile_exists'] = False
                result['response'] = {"msg": f"Profile '{module.params['name']}' not found"}
            else:
                result['profile_exists'] = True
                result['response'] = data
        except ValueError:
            logger.error(f"Invalid JSON response: {resp.text}")
            result['profile_exists'] = False
            result['response'] = {"msg": "Invalid JSON response from CC"}

        debug_info['response_status'] = resp.status_code
        debug_info['response_json'] = result['response']

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
