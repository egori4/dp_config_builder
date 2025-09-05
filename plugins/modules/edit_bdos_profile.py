# plugins/modules/manage_bdos_edit.py
"""
Unified Ansible module to edit one or multiple BDOS Flood profiles
on Radware DefensePro devices via Radware CyberController API.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: manage_bdos_edit
short_description: Edit BDOS Flood profiles on DefensePro
description:
  - Edits one or multiple BDOS Flood profiles on DefensePro devices via Radware CC API.
options:
  provider:
    description:
      - Connection details for Radware CC
    type: dict
    required: true
    suboptions:
      cc_ip:
        description: Radware CC IP
        type: str
        required: true
      username:
        type: str
        required: true
      password:
        type: str
        required: true
      log_level:
        description: Logging verbosity (disabled, info, debug)
        type: str
        required: false
        default: disabled
  dp_ip:
    description: DefensePro device IP
    type: str
    required: true
  bdos_profiles:
    description:
      - List of BDOS Flood profiles to edit with their parameters
    type: list
    required: true
    elements: dict
    suboptions:
      name:
        type: str
        required: true
      params:
        type: dict
        required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Edit multiple BDOS Flood profiles
  manage_bdos_edit:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
      log_level: debug
    dp_ip: 10.105.192.32
    bdos_profiles:
      - name: BDOS_Profile_10
        params:
          TCP Status: active
          UDP Status: inactive
      - name: BDOS_Profile_11
        params:
          TCP Status: active
          ICMP Status: active
'''

RETURN = r'''
response:
  description: API response per profile
  type: dict
debug_info:
  description: Request and response debug details
  type: dict
'''

# -------------------------------
# Field Mappings & Conversions
# -------------------------------
FIELD_MAP = {
    "TCP Status": "rsNetFloodProfileTcpStatus",
    "UDP Status": "rsNetFloodProfileUdpStatus",
    "ICMP Status": "rsNetFloodProfileIcmpStatus",
    "TCP SYN/ACK Status": "rsNetFloodProfileTcpSynAckStatus",
    "TCP Frag Status": "rsNetFloodProfileTcpFragStatus",
    "Bandwidth In": "rsNetFloodProfileBandwidthIn",
    "Bandwidth Out": "rsNetFloodProfileBandwidthOut",
    "Transparent Optimization": "rsNetFloodProfileTransparentOptimization",
    "Action": "rsNetFloodProfileAction",
    "Burst Enabled": "rsNetFloodProfileBurstEnabled",
    "Learning Suppression Threshold": "rsNetFloodProfileLearningSuppressionThreshold",
    "Footprint Strictness": "rsNetFloodProfileFootprintStrictness",
    "Rate Limit": "rsNetFloodProfileRateLimit",
    "Packet Report Status": "rsNetFloodProfilePacketReportStatus",
    "Packet Trace Status": "rsNetFloodProfilePacketTraceStatus",
}

NUMERIC_MAPPING = {
    "TCP Status": {"active": 1, "inactive": 2},
    "UDP Status": {"active": 1, "inactive": 2},
    "ICMP Status": {"active": 1, "inactive": 2},
    "TCP SYN/ACK Status": {"active": 1, "inactive": 2},
    "TCP Frag Status": {"active": 1, "inactive": 2},
    "Transparent Optimization": {"yes": 1, "no": 2},
    "Footprint Strictness": {"low": 0, "medium": 1, "high": 2},
    "Packet Report Status": {"enable": 1, "disable": 2},
    "Packet Trace Status": {"enable": 1, "disable": 2},
    "Action": {"report only": 0, "block & report": 1},
    "Burst Enabled": {"enable": 1, "disable": 2},
}

FIELD_RANGES = {
    "Learning Suppression Threshold": (0, 50),
}

# -------------------------------
# Helpers
# -------------------------------
def translate_params(params):
    translated = {}
    for k, v in params.items():
        api_key = FIELD_MAP.get(k, k)
        mapping = NUMERIC_MAPPING.get(k)
        if mapping:
            val = str(v).lower()
            if val not in mapping:
                raise ValueError(f"Invalid value '{v}' for '{k}'. Allowed: {list(mapping.keys())}")
            translated[api_key] = mapping[val]
        elif k in FIELD_RANGES:
            min_val, max_val = FIELD_RANGES[k]
            num_val = int(v)
            if not (min_val <= num_val <= max_val):
                raise ValueError(f"Field '{k}' must be in range [{min_val}..{max_val}]")
            translated[api_key] = num_val
        else:
            translated[api_key] = v
    return translated

def build_api_path(dp_ip, profile_name):
    return f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}"

# -------------------------------
# Main Logic
# -------------------------------
def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        bdos_profiles=dict(type='list', required=True),
    )

    result = dict(changed=False, response=[], debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    bdos_profiles = module.params['bdos_profiles']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    debug_info = {}

    # Validate provider fields
    for key in ('cc_ip', 'username', 'password'):
        if key not in provider or not provider[key]:
            module.fail_json(msg=f"Missing required provider field: {key}", **result)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        for profile in bdos_profiles:
            name = profile['name']
            params = profile['params']
            path = build_api_path(dp_ip, name)
            url = f"https://{provider['cc_ip']}{path}"
            body = {"rsNetFloodProfileName": name}
            body.update(translate_params(params))

            debug_info.setdefault('requests', []).append({"method": "PUT", "url": url, "body": body})
            logger.info(f"Editing BDOS profile '{name}' on {dp_ip}")

            if module.check_mode:
                result['response'].append({"profile": name, "msg": "Check mode - no changes applied"})
                continue

            try:
                resp = cc._put(url, json=body)
                debug_info.setdefault('responses', []).append({"profile": name, "status_code": resp.status_code})
                try:
                    data = resp.json()
                    debug_info.setdefault('responses_json', []).append({"profile": name, "data": data})
                except ValueError:
                    data = {"status": "unknown", "error": resp.text}

                if resp.status_code not in (200, 201):
                    result['response'].append({"profile": name, "response": data, "failed": True})
                    logger.error(f"Failed to edit BDOS profile '{name}': {data}")
                else:
                    result['response'].append({"profile": name, "response": data})
                    result['changed'] = True

            except Exception as ex:
                result['response'].append({"profile": name, "response": {"error": str(ex)}, "failed": True})
                logger.error(f"Exception editing BDOS profile '{name}': {ex}")

        # Fail module if all profiles failed
        if all(p.get('failed') for p in result['response']):
            module.fail_json(msg="All BDOS profile edits failed", **result)

        result['debug_info'] = debug_info
        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=str(e), **result)

# -------------------------------
# Entrypoint
# -------------------------------
def main():
    run_module()


if __name__ == "__main__":
    main()
