# plugins/modules/create_syn_profile.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: create_syn_profile
short_description: Create or manage DefensePro SYN Profiles
description:
  - Creates a SYN profile and attaches SYN protection in DefensePro via Radware CC API.
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
    description: Name of the SYN protection to attach
    type: str
    required: true
  params:
    description: Dictionary of profile parameters
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Create SYN Profile and Attach Protection
  create_syn_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
      verify_ssl: false
      log_level: debug
    dp_ip: 10.105.192.33
    profile_name: "Test1"
    protection_name: "TEST"
    params:
      profile_type: syn_protection
'''

RETURN = r'''
response:
  description: API response
  type: dict
debug_info:
  description: Request/response debug details
  type: dict
'''

# -------------------------------
# Field Mappings
# -------------------------------
FIELD_MAP = {"profile_type": "rsIDSSynProfileType"}
VALUE_MAP = {"profile_type": {"syn_protection": 4}}


def translate_params(params: dict) -> dict:
    """Translate friendly keys/values to API-compatible keys/values."""
    return {
        FIELD_MAP.get(k, k): VALUE_MAP.get(k, {}).get(v.lower(), v) if k in VALUE_MAP and isinstance(v, str) else v
        for k, v in params.items()
    }


def run_module():
    """Main execution for the module."""
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        profile_name=dict(type='str', required=True),
        protection_name=dict(type='str', required=True),
        params=dict(type='dict', required=True),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # Extract provider info
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
        # Connect to CC
        cc = RadwareCC(cc_ip, username, password, verify_ssl=verify_ssl, log_level=log_level, logger=logger)

        dp_ip = module.params['dp_ip']
        profile_name = module.params['profile_name']
        protection_name = module.params['protection_name']
        params = translate_params(module.params['params'])

        url = f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesTable/{profile_name}/{protection_name}"
        body = {"rsIDSSynProfilesName": profile_name, "rsIDSSynProfileServiceName": protection_name}
        body.update(params)

        debug_info = {'method': 'POST', 'url': url, 'body': body}
        logger.info(f"Creating SYN profile '{profile_name}' on {dp_ip}")
        logger.debug(f"Request: {debug_info}")

        if module.check_mode:
            module.exit_json(changed=True, response={"msg": "Check mode - no changes applied"}, debug_info=debug_info)

        resp = cc._post(url, json=body)
        try:
            data = resp.json()
        except ValueError:
            raise Exception(f"Invalid JSON response: {resp.text}")

        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to create SYN profile: {data}")

        debug_info.update({'response_status': resp.status_code, 'response_json': data})
        module.exit_json(changed=True, response=data, debug_info=debug_info)

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info)


def main():
    run_module()


if __name__ == '__main__':
    main()
