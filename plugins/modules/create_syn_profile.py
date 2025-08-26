# plugins/modules/create_syn_profile.py
from ansible.module_utils.basic import AnsibleModule  # type: ignore
from ansible.module_utils.radware_cc import RadwareCC  # type: ignore

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
      server: str
      username: str
      password: str
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
      server: 10.105.193.3
      username: radware
      password: mypass
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
'''

FIELD_MAP = {
    "profile_type": "rsIDSSynProfileType",
}

VALUE_MAP = {
    "profile_type": {
        "syn_protection": 4,  # numeric mapping
    },
}

def translate_params(params):
    translated = {}
    for k, v in params.items():
        api_key = FIELD_MAP.get(k, k)
        if k in VALUE_MAP and isinstance(v, str):
            translated[api_key] = VALUE_MAP[k].get(v.lower(), v)
        else:
            translated[api_key] = v
    return translated

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        profile_name=dict(type='str', required=True),
        protection_name=dict(type='str', required=True),
        params=dict(type='dict', required=True),
    )
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger  # type: ignore
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['server'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        if not module.check_mode:
            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsIDSSynProfilesTable/{module.params['profile_name']}/{module.params['protection_name']}"
            body = {
                "rsIDSSynProfilesName": module.params['profile_name'],
                "rsIDSSynProfileServiceName": module.params['protection_name'],
            }
            body.update(translate_params(module.params['params']))
            url = f"https://{provider['server']}{path}"

            debug_info = {'method': 'POST', 'url': url, 'body': body}
            logger.info(f"Creating SYN profile '{module.params['profile_name']}' on {module.params['dp_ip']}")
            logger.debug(f"Request: {debug_info}")

            resp = cc._post(url, json=body)
            try:
                data = resp.json()
            except ValueError:
                raise Exception(f"Invalid JSON response: {resp.text}")

            result['response'] = data
            result['changed'] = True
            debug_info['response_status'] = resp.status_code
            debug_info['response_json'] = data

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
