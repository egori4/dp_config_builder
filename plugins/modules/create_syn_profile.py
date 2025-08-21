# plugins/modules/dp_ids_syn_profile.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

DOCUMENTATION = r'''
---
module: dp_ids_syn_profile
short_description: Create or manage DefensePro IDS SYN Profiles
description:
  - Creates or updates an IDS SYN Profile on Radware DefensePro via Radware CC API.
options:
  provider:
    description:
      - Dictionary with connection parameters.
    type: dict
    required: true
    suboptions:
      server:
        description: CC IP address
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
  params:
    description:
      - Dictionary of IDS SYN Profile attributes (human-friendly keys allowed).
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Create IDS SYN Profile
  dp_ids_syn_profile:
    provider:
      server: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.33
    params:
      Profile Name: "Test1"
      Service Name: "TEST"
      Service Id: "500001"
      Profile Type: "4"
      Profile Action: "1953068832"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
'''

# Human-readable → API mapping
FIELD_MAP = {
    "Profile Name": "rsIDSSynProfilesName",
    "Service Name": "rsIDSSynProfileServiceName",
    "Service Id": "rsIDSSynProfileServiceId",
    "Profile Type": "rsIDSSynProfileType",
    "Profile Action": "rsIDSSynProfileAction"
}

def translate_params(params):
    translated = {}
    for k, v in params.items():
        translated[FIELD_MAP.get(k, k)] = v
    return translated

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        params=dict(type='dict', required=True)
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')

    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['server'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        params = translate_params(module.params['params'])
        profile_name = params["rsIDSSynProfilesName"]
        service_name = params["rsIDSSynProfileServiceName"]

        path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsIDSSynProfilesTable/{profile_name}/{service_name}"
        url = f"https://{provider['server']}{path}"

        if not module.check_mode:
            debug_info = {
                'method': 'POST',
                'url': url,
                'body': params
            }
            logger.info(f"Creating IDS SYN Profile {profile_name}/{service_name} on device {module.params['dp_ip']}")
            logger.debug(f"Request: {debug_info}")

            resp = cc._post(url, json=params)
            logger.debug(f"Response status: {resp.status_code}")

            try:
                data = resp.json()
                logger.debug(f"Response JSON: {data}")
            except ValueError:
                raise Exception(f"Invalid JSON response: {resp.text}")

            result['response'] = data
            result['changed'] = True
            debug_info['response_status'] = resp.status_code
            debug_info['response_json'] = data

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
