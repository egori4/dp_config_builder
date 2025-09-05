# plugins/modules/manage_bdos_profiles.py
"""
Unified Ansible module to manage multiple BDOS Flood profiles on DefensePro devices.

- Accepts a list of BDOS profiles to create/update in a single device.
- Supports check mode, logging, and structured output with debug info.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

# -------------------------------
# Field mappings and numeric mappings
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
    "Action": {"report only": 0, "block & report": 1},
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
    translated = {}
    for k, v in params.items():
        api_key = FIELD_MAP.get(k, k)
        mapping = NUMERIC_MAPPING.get(k)
        val = v.lower() if isinstance(v, str) else v
        if mapping:
            if val not in mapping:
                raise ValueError(f"Invalid value '{v}' for '{k}'. Allowed: {list(mapping.keys())}")
            translated[api_key] = mapping[val]
        else:
            translated[api_key] = v
    return translated

def build_api_path(dp_ip, name):
    return f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{name}"

# -------------------------------
# Main Module Logic
# -------------------------------
def run_module():
    debug_info = {}  # ✅ Ensure debug_info is defined before try
    result = dict(changed=False, response={}, debug_info=debug_info)

    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        bdos_profiles=dict(type='list', required=True)  # required, no default
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params.get('provider', {})
    dp_ip = module.params.get('dp_ip', '')
    bdos_profiles = module.params.get('bdos_profiles', [])

    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    debug_info['input'] = {'dp_ip': dp_ip, 'profiles_count': len(bdos_profiles)}

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        created_profiles = []
        changes_made = False

        if module.check_mode:
            result['changed'] = bool(bdos_profiles)
            result['response'] = {'would_create_profiles': bdos_profiles}
            module.exit_json(**result)

        for profile in bdos_profiles:
            name = profile['name']
            params = translate_params(profile.get('params', {}))
            path = build_api_path(dp_ip, name)
            url = f"https://{provider['cc_ip']}{path}"

            body = {"rsNetFloodProfileName": name}
            body.update(params)

            logger.info(f"Creating BDOS profile '{name}' on {dp_ip}")
            resp = cc._post(url, json=body)
            data = resp.json()

            if resp.status_code not in (200, 201):
                raise Exception(f"Failed to create/update BDOS profile '{name}': {data}")

            created_profiles.append({'profile_name': name, 'response': data})
            changes_made = True

        result['changed'] = changes_made
        result['response'] = {'created_profiles': created_profiles}
        debug_info['summary'] = {'profiles_created': len(created_profiles), 'operations_completed': changes_made}

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    module.exit_json(**result)

# -------------------------------
# Entrypoint
# -------------------------------
def main():
    run_module()

if __name__ == "__main__":
    main()
