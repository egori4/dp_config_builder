# plugins/modules/edit_syn_protection.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: edit_syn_protection
short_description: Edit an existing IDS SYN Protection on a DefensePro device
description:
  - Updates an existing SYN protection on Radware DefensePro via Radware CC API using HTTP PUT.
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
  protection_id:
    description: Numeric protection ID (row index in rsIDSSYNAttackTable)
    type: int
    required: true
  params:
    description: Dictionary of SYN protection parameters to update
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Edit SYN Protection
  edit_syn_protection:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
      verify_ssl: false
      log_level: debug
    dp_ip: 155.1.1.7
    protection_id: 0
    params:
      app_port_group: http
      activation_threshold: 3000
      termination_threshold: 2000
      packet_report: enable
'''

RETURN = r'''
response:
  description: API response
  type: dict
debug_info:
  description: Request/response debug details
  type: dict
'''

# Mapping human-readable keys to API fields
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
        protection_id=dict(type='int', required=True),
        params=dict(type='dict', required=True),
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
        protection_id = module.params['protection_id']
        params = translate_params(module.params['params'])

        url = f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/{protection_id}"
        debug_info = {'method': 'PUT', 'url': url, 'body': params}

        logger.info(f"Editing SYN protection ID {protection_id} on device {dp_ip}")
        logger.debug(f"Request: {debug_info}")

        if module.check_mode:
            module.exit_json(changed=True, response={"msg": "Check mode - no changes applied"}, debug_info=debug_info)

        resp = cc._put(url, json=params)
        resp.raise_for_status()

        try:
            data = resp.json()
        except ValueError:
            raise Exception(f"Invalid JSON response: {resp.text}")

        debug_info.update({'response_status': resp.status_code, 'response_json': data})
        module.exit_json(changed=True, response=data, debug_info=debug_info)

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info)

def main():
    run_module()

if __name__ == '__main__':
    main()
