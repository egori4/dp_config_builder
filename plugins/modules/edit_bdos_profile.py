from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: dp_bdos_profile
short_description: Manage DefensePro BDOS Flood profiles via Radware CC
description:
  - Creates or updates BDOS Flood profiles on Radware DefensePro devices using Radware CC API.
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
        default: disabled
  dp_ip:
    description: DefensePro device IP address
    type: str
    required: true
  name:
    description: BDOS Flood profile name
    type: str
    required: true
  params:
    description:
      - Dictionary of BDOS Flood profile attributes and values
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Create or update BDOS Flood profile (PUT)
  dp_bdos_profile:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
      log_level: debug
    dp_ip: 155.1.1.7
    name: "BDOS_Test"
    params:
      TCP Status: "active"
      UDP Status: "inactive"
      Transparent Optimization: "yes"
      Footprint Strictness: "medium"
      Action: "block & report"
      Burst Enabled: "enable"
      Rate Limit: "normalEdge"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
debug_info:
  description: Request and response debug details
  type: dict
'''

# -------------------------------
# Field Mappings and Numeric Mapping
# -------------------------------
FIELD_MAP = { ... }  # same as your current FIELD_MAP
NUMERIC_MAPPING = { ... }  # same as your current NUMERIC_MAPPING

# -------------------------------
# Helpers
# -------------------------------
def translate_params(params):
    translated = {}
    for k, v in params.items():
        api_key = FIELD_MAP.get(k, k)
        mapping = NUMERIC_MAPPING.get(k)
        val = v.lower() if isinstance(v, str) else v
        if mapping:
            if val not in mapping:
                raise ValueError(
                    f"Invalid value '{v}' for '{k}'. Allowed: {list(mapping.keys())}"
                )
            translated[api_key] = mapping[val]
        else:
            translated[api_key] = v
    return translated

def build_api_path(dp_ip, name):
    return f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{name}"

# -------------------------------
# Main Logic
# -------------------------------
def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=True),
        params=dict(type='dict', required=True),
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

        path = build_api_path(dp_ip, name)
        url = f"https://{provider['cc_ip']}{path}"

        body = {"rsNetFloodProfileName": name}
        body.update(translate_params(module.params['params']))

        debug_info['request'] = {"method": "PUT", "url": url, "body": body}
        logger.info(f"Updating BDOS Flood profile '{name}' on {dp_ip} via PUT")

        if module.check_mode:
            result['changed'] = True
            result['response'] = {"msg": "Check mode - no changes applied"}
        else:
            # Explicitly use PUT
            put_method = getattr(cc, "put", cc._put)
            resp = put_method(url, json=body)

            debug_info['response_status'] = resp.status_code
            try:
                data = resp.json()
                debug_info['response_json'] = data
            except ValueError:
                raise Exception(f"Invalid JSON response: {resp.text}")

            if resp.status_code not in (200, 201):
                raise Exception(f"Failed to update BDOS profile: {data}")

            result['changed'] = True
            result['response'] = data

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == "__main__":
    main()
