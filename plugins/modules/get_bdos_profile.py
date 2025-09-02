# plugins/modules/get_bdos_profile.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: get_bdos_profile
short_description: Fetch BDOS Flood profiles from a DefensePro device via Radware CC
description:
  - Retrieves BDOS Flood profiles from DefensePro devices using Radware CC API
options:
  provider:
    description:
      - Dictionary with connection parameters for Radware CC.
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
        description: Log verbosity level (enabled/disabled/debug)
        type: str
        required: false
        default: disabled
  dp_ip:
    description: DefensePro device IP address
    type: str
    required: true
  profile_name:
    description: Optional BDOS profile name to fetch. If omitted, fetches all profiles.
    type: str
    required: false
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Fetch all BDOS profiles
  get_bdos_profile:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7

- name: Fetch a specific BDOS profile
  get_bdos_profile:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    profile_name: "BDOS_Test"
'''

RETURN = r'''
response:
  description: API response from Radware CC containing BDOS profile(s)
  type: dict
debug_info:
  description: Request and response debug details
  type: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        profile_name=dict(type='str', required=False, default=None),
    )

    result = dict(changed=False, response={}, debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    profile_name = module.params.get('profile_name')
    log_level = provider.get('log_level', 'disabled')

    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        # Build URL
        if profile_name:
            path = f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}"
        else:
            path = f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable"

        url = f"https://{provider['cc_ip']}{path}"
        debug_info = {'method': 'GET', 'url': url, 'body': None}
        logger.info(f"Fetching BDOS profile(s) from device {dp_ip}")
        logger.debug(f"GET URL: {url}")

        # Lock device to ensure consistency (optional for GET, can remove if not required)
        # logger.info(f"Locking device {dp_ip}")
        # cc._post(f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/lock")

        resp = cc._get(url)
        debug_info['response_status'] = resp.status_code

        try:
            data = resp.json()
            result['response'] = data
            debug_info['response_json'] = data
            logger.debug(f"Response JSON: {data}")
        except ValueError:
            logger.error(f"Invalid JSON response: {resp.text}")
            module.fail_json(msg="Invalid JSON response", response_text=resp.text, debug_info=debug_info)

        # Unlock device if locking was used
        # logger.info(f"Unlocking device {dp_ip}")
        # cc._post(f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/unlock")

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
