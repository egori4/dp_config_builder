# plugins/modules/delete_syn_profile.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: delete_syn_profile
short_description: Delete a SYN Profile from a DefensePro device
description:
  - Deletes a SYN profile/service from a DefensePro device via Radware CC API.
options:
  provider:
    description: Radware CC connection details
    type: dict
    required: true
    suboptions:
      cc_ip: str
      username: str
      password: str
      verify_ssl: bool
      log_level: str
  dp_ip:
    description: DefensePro device IP
    type: str
    required: true
  profile_name:
    description: Name of the SYN profile
    type: str
    required: true
  protection_name:
    description: Name of the attached SYN protection
    type: str
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Delete SYN Profile
  delete_syn_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
      verify_ssl: false
      log_level: debug
    dp_ip: 10.105.192.33
    profile_name: "Test1"
    protection_name: "TEST"
'''

RETURN = r'''
response:
  description: API response
  type: dict
debug_info:
  description: Request/response debug details
  type: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        profile_name=dict(type='str', required=True),
        protection_name=dict(type='str', required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    cc_ip = provider.get('cc_ip')
    username = provider.get('username')
    password = provider.get('password')
    verify_ssl = provider.get('verify_ssl', False)
    log_level = provider.get('log_level', 'disabled')

    if not all([cc_ip, username, password]):
        module.fail_json(msg="provider.cc_ip, provider.username, and provider.password are required")

    logger = Logger(verbosity=log_level)
    debug_info = {}

    try:
        cc = RadwareCC(cc_ip, username, password, verify_ssl=verify_ssl, log_level=log_level, logger=logger)

        dp_ip = module.params['dp_ip']
        profile_name = module.params['profile_name']
        protection_name = module.params['protection_name']

        url = f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesTable/{profile_name}/{protection_name}"
        debug_info = {'method': 'DELETE', 'url': url, 'body': None}

        logger.info(f"Deleting SYN Profile '{profile_name}/{protection_name}' on device {dp_ip}")
        logger.debug(f"Request: {debug_info}")

        if module.check_mode:
            module.exit_json(changed=True, response={"msg": "Check mode - no changes applied"}, debug_info=debug_info)

        resp = cc._delete(url)
        try:
            resp.raise_for_status()
        except Exception:
            # If the profile does not exist, handle gracefully
            module.exit_json(changed=False, response={"msg": "Profile not found"}, debug_info=debug_info)

        try:
            data = resp.json()
        except ValueError:
            data = {"raw_response": resp.text}

        debug_info.update({'response_status': resp.status_code, 'response_json': data})
        module.exit_json(changed=True, response=data, debug_info=debug_info)

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info)


def main():
    run_module()


if __name__ == '__main__':
    main()
