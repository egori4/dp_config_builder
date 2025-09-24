from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

DOCUMENTATION = r'''
---
module: create_syn_protection
short_description: Create or manage DefensePro SYN Flood protections
description:
  - Creates a SYN Flood protection on Radware DefensePro via Radware CC API.
  - Supports human-readable keys/values mapped to numeric API codes.
options:
  provider:
    description: Radware CC connection details
    type: dict
    required: true
  dp_ip:
    description: DefensePro device IP
    type: str
    required: true
  name:
    description: Name of the SYN protection
    type: str
    required: true
  params:
    description: Dictionary of protection parameters (human-readable keys)
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Create SYN Protection
  create_syn_protection:
    provider:
      server: 10.1.1.6
      username: radware
      password: mypass
    dp_ip: 10.1.1.7
    name: "SYN_PROT_1"
    params:
      activation_threshold: 2500
      termination_threshold: 1500
      app_port_group: http
      packet_report: enable
'''

RETURN = r'''
response:
  description: API response
  type: dict
'''

FIELD_MAP = {
    "activation_threshold": "rsIDSSYNAttackActivationThreshold",
    "termination_threshold": "rsIDSSYNAttackTerminationThreshold",
    "app_port_group": "rsIDSSYNDestinationAppPortGroup",
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
        provider=dict(type="dict", required=True),
        dp_ip=dict(type="str", required=True),
        name=dict(type="str", required=True),
        params=dict(type="dict", required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    result = dict(changed=False, response={})
    debug_info = {}

    provider = module.params["provider"]
    dp_ip = module.params["dp_ip"]
    name = module.params["name"]
    params = module.params["params"]

    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=provider.get("log_level", "disabled"))

    try:
        cc = RadwareCC(provider["server"], provider["username"], provider["password"], log_level=provider.get("log_level", "disabled"), logger=logger)

        # Check if protection already exists
        existing_url = f"https://{provider['server']}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable"
        existing_resp = cc._get(existing_url)
        existing_names = [p["rsIDSSYNAttackName"] for p in existing_resp.json().get("rsIDSSYNAttackTable", [])]

        if name in existing_names:
            logger.info(f"SYN Protection '{name}' already exists on {dp_ip}. Skipping creation.")
            result["response"] = {"status": "exists"}
        else:
            if not module.check_mode:
                path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/0/"
                body = {"rsIDSSYNAttackName": name}
                body.update(translate_params(params))
                url = f"https://{provider['server']}{path}"
                debug_info = {"method": "POST", "url": url, "body": body}
                logger.info(f"Creating SYN protection '{name}' on {dp_ip}")
                resp = cc._post(url, json=body)
                resp.raise_for_status()
                result["changed"] = True
                result["response"] = resp.json()
                debug_info["response_status"] = resp.status_code
                debug_info["response_json"] = resp.json()

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result["debug_info"] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == "__main__":
    main()
