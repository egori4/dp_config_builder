#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: dp_oos_profile
short_description: Create or manage DefensePro OOS (Stateful) profiles
description:
  - Creates an OOS / Stateful profile on Radware DefensePro via Radware CC API.
options:
  provider:
    description:
      - Dictionary with connection parameters.
    type: dict
    required: true
    suboptions:
      cc_ip:
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
  name:
    type: str
    required: true
  params:
    description:
      - Dictionary of Stateful profile attributes
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Create OOS profile
  dp_oos_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: radware
    dp_ip: 10.105.192.32
    name: "Test1"
    params:
      Act Threshold: "5000"
      Term Threshold: "4000"
      Syn-Ack Allow: "enable"
      Packet Trace Status: "enable"
      Packet Report Status: "enable"
      Risk Level: "medium"
      Profile Action: "block"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
'''

# Mapping user-friendly → API integer values (do not change)
PARAM_MAP = {
    "Syn-Ack Allow": {"enable": 1, "disable": 2},
    "Packet Trace Status": {"enable": 1, "disable": 2},
    "Packet Report Status": {"enable": 1, "disable": 2},
    "Risk Level": {"low": 1, "medium": 2, "high": 3},
    "Profile Action": {"allow": 0, "block": 1},
}

# Mapping user-friendly keys → API field names (do not change)
FIELD_MAP = {
    "Act Threshold": "rsSTATFULProfileactThreshold",
    "Term Threshold": "rsSTATFULProfiletermThreshold",
    "Syn-Ack Allow": "rsSTATFULProfilesynAckAllow",
    "Packet Trace Status": "rsSTATFULProfilePacketTraceStatus",
    "Packet Report Status": "rsSTATFULProfilePacketReportStatus",
    "Risk Level": "rsSTATFULProfileRisk",
    "Profile Action": "rsSTATFULProfileAction",
}

def translate_params(params):
    """Convert user-friendly params to API-ready integer fields."""
    return {
        FIELD_MAP.get(k, k): (PARAM_MAP[k].get(v, v) if k in PARAM_MAP else v)
        for k, v in params.items()
    }

def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            provider=dict(type='dict', required=True),
            dp_ip=dict(type='str', required=True),
            name=dict(type='str', required=True),
            params=dict(type='dict', required=True),
        ),
        supports_check_mode=True,
    )

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    name = module.params['name']
    params = module.params['params']

    logger = Logger(verbosity=provider.get('log_level', 'disabled'))

    result = dict(changed=False, response={})
    debug_info = {}

    try:
        cc = RadwareCC(
            provider['cc_ip'],
            provider['username'],
            provider['password'],
            log_level=provider.get('log_level', 'disabled'),
            logger=logger,
        )

        if not module.check_mode:
            path = f"/mgmt/device/byip/{dp_ip}/config/rsStatefulProfileTable/{name}"
            url = f"https://{provider['cc_ip']}{path}"
            body = {"rsSTATFULProfileName": name, **translate_params(params)}

            debug_info.update(method="POST", url=url, body=body)
            logger.info(f"Creating OOS Stateful profile '{name}' on device {dp_ip}")
            logger.debug(f"Request: {debug_info}")

            resp = cc._post(url, json=body)
            debug_info["response_status"] = resp.status_code

            # Treat non-2xx as errors with context
            if resp.status_code not in (200, 201):
                payload = resp.text
                try:
                    payload = resp.json()
                except Exception:
                    pass
                debug_info["response_error"] = payload
                raise Exception(f"API error {resp.status_code}: {payload}")

            # Safe JSON parse with fallback
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
