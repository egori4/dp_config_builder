# plugins/modules/create_syn_protection.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

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
      cc_ip: str
      username: str
      password: str
      verify_ssl: bool
      log_level: str
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
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
      verify_ssl: false
      log_level: debug
    dp_ip: 10.105.192.33
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
debug_info:
  description: Request/response debug details
  type: dict
'''

# -------------------------------
# Field Mappings
# -------------------------------
FIELD_MAP = {
    "app_port_group": "rsIDSSYNDestinationAppPortGroup",
    "activation_threshold": "rsIDSSYNAttackActivationThreshold",
    "termination_threshold": "rsIDSSYNAttackTerminationThreshold",
    "packet_report": "rsIDSSYNAttackPacketReport",
}

VALUE_MAP = {
    "packet_report": {"enable": 1, "disable": 2},
}

def translate_params(params: dict) -> dict:
    """Translate human-readable params to API-compatible keys/values."""
    return {
        FIELD_MAP.get(k, k): VALUE_MAP.get(k, {}).get(v.lower(), v) if k in VALUE_MAP and isinstance(v, str) else v
        for k, v in params.items()
    }


def run_module():
    """Main module logic."""
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=True),
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
        protection_name = module.params['name']
        params = translate_params(module.params['params'])

        url = f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/0"
        body = {"rsIDSSYNAttackName": protection_name}
        body.update(params)

        debug_info = {'method': 'POST', 'url': url, 'body': body}
        logger.info(f"Creating SYN protection '{protection_name}' on {dp_ip}")
        logger.debug(f"Request: {debug_info}")

        if module.check_mode:
            module.exit_json(changed=True, response={"msg": "Check mode - no changes applied"}, debug_info=debug_info)

        resp = cc._post(url, json=body)
        try:
            data = resp.json()
        except ValueError:
            raise Exception(f"Invalid JSON response: {resp.text}")

        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to create SYN protection: {data}")

        debug_info.update({'response_status': resp.status_code, 'response_json': data})
        module.exit_json(changed=True, response=data, debug_info=debug_info)

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info)


def main():
    run_module()


if __name__ == '__main__':
    main()
