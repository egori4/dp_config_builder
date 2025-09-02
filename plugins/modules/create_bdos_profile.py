# plugins/modules/dp_bdos_profile.py

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
        required: false
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
- name: Create BDOS Flood profile
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
      Action: "block"
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
# Field Mappings
# -------------------------------
FIELD_MAP = {
    "TCP Status": "rsNetFloodProfileTcpStatus",
    "TCP SYN Status": "rsNetFloodProfileTcpSynStatus",
    "UDP Status": "rsNetFloodProfileUdpStatus",
    "IGMP Status": "rsNetFloodProfileIgmpStatus",
    "ICMP Status": "rsNetFloodProfileIcmpStatus",
    "TCP FIN/ACK Status": "rsNetFloodProfileTcpFinAckStatus",
    "TCP RST Status": "rsNetFloodProfileTcpRstStatus",
    "TCP PSH/ACK Status": "rsNetFloodProfileTcpPshAckStatus",
    "TCP SYN/ACK Status": "rsNetFloodProfileTcpSynAckStatus",
    "TCP Frag Status": "rsNetFloodProfileTcpFragStatus",
    "UDP Frag Status": "rsNetFloodProfileUdpFragStatus",
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
    "Simulation Stop At Attack End": "rsNetFloodProfileSimulationStopAtAttackEnd",
    "Simulation Start When Sig Change": "rsNetFloodProfileSimulationStartWhenSigChange",
    "Joint Distribution Status": "rsNetFloodProfileJointDistributionStatus",
    "Advanced UDP Detection": "rsNetFloodProfileAdvUdpDetection",
    "Advanced UDP Learning Period": "rsNetFloodProfileAdvUdpLearningPeriod",
    "Over Mitigation Status": "rsNetFloodProfileOverMitigationStatus",
    "Level Of Regularization": "rsNetFloodProfileLevelOfReuglarzation"
}

NUMERIC_MAPPING = {
    "TCP Status": {"active": 1, "inactive": 2},
    "TCP SYN Status": {"active": 1, "inactive": 2},
    "UDP Status": {"active": 1, "inactive": 2},
    "IGMP Status": {"active": 1, "inactive": 2},
    "ICMP Status": {"active": 1, "inactive": 2},
    "TCP FIN/ACK Status": {"active": 1, "inactive": 2},
    "TCP RST Status": {"active": 1, "inactive": 2},
    "TCP PSH/ACK Status": {"active": 1, "inactive": 2},
    "TCP SYN/ACK Status": {"active": 1, "inactive": 2},
    "TCP Frag Status": {"active": 1, "inactive": 2},
    "UDP Frag Status": {"active": 1, "inactive": 2},
    "Transparent Optimization": {"yes": 1, "no": 2},
    "Footprint Strictness": {"low": 0, "medium": 1, "high": 2},
    "Packet Report Status": {"enable": 1, "disable": 2},
    "Packet Trace Status": {"enable": 1, "disable": 2},
    "Action": {"report": 0, "block": 1, "block & report": 1},
    "Burst Enabled": {"enable": 1, "disable": 2},
    "Rate Limit": {"disable": 0, "normalEdge": 1, "suspectEdge": 2, "userDefined": 3},
    "Simulation Stop At Attack End": {"false": 0, "true": 1},
    "Simulation Start When Sig Change": {"false": 0, "true": 1},
    "Joint Distribution Status": {"enable": 1, "disable": 2},
    "Advanced UDP Detection": {"enable": 1, "disable": 2},
    "Advanced UDP Learning Period": {"sixhours": 1, "oneday": 2, "threedays": 3},
    "Over Mitigation Status": {"enable": 1, "disable": 2},
    "Level Of Regularization": {"notapplied": 1, "weak": 2, "middle": 3, "strong": 4},
}

# -------------------------------
# Helpers
# -------------------------------
def translate_params(params):
    """Translate user-friendly values to API numeric values using NUMERIC_MAPPING."""
    translated = {}
    for k, v in params.items():
        api_key = FIELD_MAP.get(k, k)
        mapping = NUMERIC_MAPPING.get(k)

        # normalize strings
        val = v.lower() if isinstance(v, str) else v

        if mapping:
            if val not in mapping:
                raise ValueError(
                    f"Invalid value '{v}' for parameter '{k}'. Allowed: {list(mapping.keys())}"
                )
            translated[api_key] = mapping[val]
        else:
            translated[api_key] = v
    return translated

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
    log_level = provider.get('log_level', 'disabled')

    logger = Logger(verbosity=log_level)
    debug_info = {}

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        if not module.check_mode:
            path = (
                f"/mgmt/device/byip/{module.params['dp_ip']}"
                f"/config/rsNetFloodProfileTable/{module.params['name']}"
            )
            body = {"rsNetFloodProfileName": module.params['name']}
            body.update(translate_params(module.params['params']))

            url = f"https://{provider['cc_ip']}{path}"
            debug_info['request'] = {"method": "POST", "url": url, "body": body}
            logger.info(f"Creating BDOS Flood profile '{module.params['name']}' on {module.params['dp_ip']}")

            # Prefer public request method instead of _post
            resp = cc.post(url, json=body) if hasattr(cc, "post") else cc._post(url, json=body)

            debug_info['response_status'] = resp.status_code
            try:
                data = resp.json()
                debug_info['response_json'] = data
            except ValueError:
                raise Exception(f"Invalid JSON response: {resp.text}")

            if resp.status_code not in (200, 201):
                raise Exception(f"Failed to create BDOS profile: {data}")

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
