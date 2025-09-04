# plugins/modules/edit_oos_profile.py
"""
Ansible module to edit an existing OOS (Stateful) profile on Radware DefensePro via CyberController API.

This module allows you to update an existing Stateful profile on a specific DefensePro device.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: edit_oos_profile
short_description: Edit existing DefensePro OOS Stateful profiles
description:
  - Updates an existing OOS (Stateful) profile on a Radware DefensePro device via CyberController API.
options:
  provider:
    description:
      - Dictionary with connection parameters for the CyberController
    type: dict
    required: true
    suboptions:
      cc_ip:
        description: CyberController IP
        type: str
        required: true
      username:
        type: str
        required: true
      password:
        type: str
        required: true
      log_level:
        type: str
        required: false
        default: "disabled"
  dp_ip:
    description:
      - Target DefensePro IP
    type: str
    required: true
  name:
    description:
      - Name of the OOS profile to edit
    type: str
    required: true
  params:
    description:
      - Dictionary of OOS profile parameters to update
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Edit OOS profile
  edit_oos_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: radware
      log_level: debug
    dp_ip: 10.105.192.32
    name: "OOS_Profile_1"
    params:
      Act Threshold: "6000"
      Term Threshold: "5000"
      Syn-Ack Allow: "disable"
      Packet Trace Status: "enable"
      Packet Report Status: "disable"
      Action: "block & report"
'''

RETURN = r'''
response:
  description: API response from CyberController
  type: dict
'''

# Mapping user-friendly values to API integers
PARAM_MAP = {
    "Syn-Ack Allow": {"enable": 1, "disable": 2},
    "Packet Trace Status": {"enable": 1, "disable": 2},
    "Packet Report Status": {"enable": 1, "disable": 2},
    "Action": {"report": 0,"block & report": 1},
}

# Mapping user-friendly keys to API field names
FIELD_MAP = {
    "Act Threshold": "rsSTATFULProfileactThreshold",
    "Term Threshold": "rsSTATFULProfiletermThreshold",
    "Syn-Ack Allow": "rsSTATFULProfilesynAckAllow",
    "Packet Trace Status": "rsSTATFULProfilePacketTraceStatus",
    "Packet Report Status": "rsSTATFULProfilePacketReportStatus",
    "Action": "rsSTATFULProfileAction",
}

def translate_params(params):
    """Translate user-friendly keys/values into API-ready fields"""
    return {FIELD_MAP.get(k, k): PARAM_MAP[k].get(v, v) if k in PARAM_MAP else v for k, v in params.items()}

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
    dp_ip = module.params['dp_ip']
    name = module.params['name']
    params = module.params['params']
    logger = Logger(verbosity=provider.get('log_level', 'disabled'))

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                        log_level=provider.get('log_level', 'disabled'), logger=logger)

        if not module.check_mode:
            path = f"/mgmt/device/byip/{dp_ip}/config/rsStatefulProfileTable/{name}"
            url = f"https://{provider['cc_ip']}{path}"
            body = {"rsSTATFULProfileName": name, **translate_params(params)}

            debug_info.update(method="PUT", url=url, body=body)
            logger.info(f"Editing OOS Stateful profile '{name}' on device {dp_ip}")
            logger.debug(f"Request: {debug_info}")

            resp = cc._put(url, json=body)
            debug_info["response_status"] = resp.status_code

            if resp.status_code not in (200, 201):
                payload = resp.text
                try:
                    payload = resp.json()
                except Exception:
                    pass
                debug_info["response_error"] = payload
                raise Exception(f"API error {resp.status_code}: {payload}")

            if resp.headers.get("Content-Type", "").lower().startswith("application/json"):
                data = resp.json()
            else:
                data = {"raw": resp.text}

            debug_info["response_json"] = data
            result.update(changed=True, response=data)

    except Exception as e:
        logger.error(f"Exception: {e}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result["debug_info"] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
