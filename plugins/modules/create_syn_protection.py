# plugins/modules/create_syn_protection.py
from ansible.module_utils.basic import AnsibleModule  # type: ignore
from ansible.module_utils.radware_cc import RadwareCC  # type: ignore

DOCUMENTATION = r'''
---
module: create_syn_protection
short_description: Create or manage DefensePro IDS SYN Flood protection
description:
  - Creates a SYN Flood protection on Radware DefensePro via Radware CC API.
  - Supports human-readable keys/values mapped to numeric API codes.
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
  name:
    description: Name of the SYN protection
    type: str
    required: true
  params:
    description: Dictionary of SYN protection parameters (human-readable keys)
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Create SYN Protection
  create_syn_protection:
    provider:
      server: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    name: "TEST"
    params:
      app_port_group: http
      activation_threshold: 2500
      termination_threshold: 1500
      packet_report: enable
'''

RETURN = r'''
response:
  description: API response
  type: dict
'''

FIELD_MAP = {
    "app_port_group": "rsIDSSYNDestinationAppPortGroup",
    "activation_threshold": "rsIDSSYNAttackActivationThreshold",
    "termination_threshold": "rsIDSSYNAttackTerminationThreshold",
    "packet_report": "rsIDSSYNAttackPacketReport",
}

VALUE_MAP = {
    "packet_report": {"enable": 1, "disable": 2},
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
        name=dict(type='str', required=True),
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
            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsIDSSYNAttackTable/0"
            body = {"rsIDSSYNAttackName": module.params['name']}
            body.update(translate_params(module.params['params']))
            url = f"https://{provider['server']}{path}"

            debug_info = {'method': 'POST', 'url': url, 'body': body}
            logger.info(f"Creating SYN protection '{module.params['name']}' on {module.params['dp_ip']}")
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
