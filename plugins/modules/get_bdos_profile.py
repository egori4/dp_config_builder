# plugins/modules/get_bdos_profile.py
"""
Ansible module to fetch DefensePro BDOS profiles via CyberController API.

- Fetches all BDOS (NetFlood) profiles from a DefensePro device.
- Maps API response values back to user-friendly keys (reverse of create/edit logic).
- Returns structured response with raw, formatted, and summary data.
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC

# Reverse mapping from API field names to user-friendly names
REVERSE_FIELD_MAP = {
    "rsNetFloodProfileTcpSynStatus": "syn_flood",
    "rsNetFloodProfileUdpStatus": "udp_flood",
    "rsNetFloodProfileIgmpStatus": "igmp_flood",
    "rsNetFloodProfileIcmpStatus": "icmp_flood",
    "rsNetFloodProfileTcpFinAckStatus": "tcp_ack_fin_flood",
    "rsNetFloodProfileTcpRstStatus": "tcp_rst_flood",
    "rsNetFloodProfileTcpPshAckStatus": "tcp_psh_ack_flood",
    "rsNetFloodProfileTcpSynAckStatus": "tcp_syn_ack_flood",
    "rsNetFloodProfileTcpFragStatus": "tcp_frag_flood",
    "rsNetFloodProfileUdpFragStatus": "udp_frag_flood",
    "rsNetFloodProfileTransparentOptimization": "transparent_optimization",
    "rsNetFloodProfileAction": "action",
    "rsNetFloodProfileBurstEnabled": "burst_attack",
    "rsNetFloodProfileFootprintStrictness": "footprint_strictness",
    "rsNetFloodProfileRateLimit": "bdos_rate_limit",
    "rsNetFloodProfilePacketReportStatus": "packet_report",
    "rsNetFloodProfileLevelOfReuglarzation": "udp_packet_rate_detection_sensitivity",
    "rsNetFloodProfileAdvUdpDetection": "adv_udp_detection",
    "rsNetFloodProfileBandwidthIn": "inbound_traffic",
    "rsNetFloodProfileBandwidthOut": "outbound_traffic",
    "rsNetFloodProfileTcpInQuota": "tcp_in_quota",
    "rsNetFloodProfileUdpInQuota": "udp_in_quota",
    "rsNetFloodProfileIcmpInQuota": "icmp_in_quota",
    "rsNetFloodProfileIgmpInQuota": "igmp_in_quota",
    "rsNetFloodProfileTcpOutQuota": "tcp_out_quota",
    "rsNetFloodProfileUdpOutQuota": "udp_out_quota",
    "rsNetFloodProfileIcmpOutQuota": "icmp_out_quota",
    "rsNetFloodProfileIgmpOutQuota": "igmp_out_quota",
    "rsNetFloodProfileNoBurstTimeout": "maximum_interval_between_bursts",
    "rsNetFloodProfileLearningSuppressionThreshold": "learning_suppression_threshold",
    "rsNetFloodProfileUserDefinedRateLimit": "user_defined_rate_limit",
    "rsNetFloodProfileUserDefinedRateLimitUnit": "user_defined_rate_limit_unit"
}

# Map API numeric values to user-friendly strings
REVERSE_ENUM_MAPS = {
    "rsNetFloodProfileTcpSynStatus": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileUdpStatus": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileIgmpStatus": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileIcmpStatus": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileTcpFinAckStatus": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileTcpRstStatus": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileTcpPshAckStatus": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileTcpSynAckStatus": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileTcpFragStatus": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileUdpFragStatus": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileTransparentOptimization": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileBurstEnabled": {"1": "enable", "2": "disable"},
    "rsNetFloodProfilePacketReportStatus": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileAdvUdpDetection": {"1": "enable", "2": "disable"},
    "rsNetFloodProfileFootprintStrictness": {"0": "low", "1": "medium", "2": "high"},
    "rsNetFloodProfileUserDefinedRateLimitUnit": {"0": "kbps", "1": "mbps", "2": "gbps"},
    "rsNetFloodProfileLevelOfReuglarzation": {"1": "ignore", "2": "low", "3": "medium", "4": "high"},
    "rsNetFloodProfileRateLimit": {"0": "disable", "1": "normal_edge", "2": "suspect_edge", "3": "user_defined"},
    "rsNetFloodProfileAction": {"0": "report_only", "1": "block_and_report"}
}

def format_bdos_profile_for_display(raw_profile_data):
    """
    Convert raw BDOS API data into user-friendly dictionary
    """
    formatted = {"profile_name": raw_profile_data.get("rsNetFloodProfileName", "N/A")}
    for api_field, user_field in REVERSE_FIELD_MAP.items():
        value = raw_profile_data.get(api_field)
        if value is None:
            continue
        if api_field in REVERSE_ENUM_MAPS:
            formatted[user_field] = REVERSE_ENUM_MAPS[api_field].get(str(value), value)
        else:
            formatted[user_field] = value
    return formatted

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        filter_bdos_profile_names=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    filter_bdos_profile_names = module.params['filter_bdos_profile_names']

    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                   log_level=log_level, logger=logger)

    try:
        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable"
        logger.info(f"Fetching BDOS profiles from device {dp_ip}")
        resp = cc._get(url)
        data = resp.json()

        profiles_raw = data.get('rsNetFloodProfileTable', [])
        debug_info['profiles_raw_count'] = len(profiles_raw)

        # Apply filter if provided
        if filter_bdos_profile_names:
            profiles_raw = [p for p in profiles_raw if p.get('rsNetFloodProfileName') in filter_bdos_profile_names]
            logger.info(f"Filtered profiles to: {filter_bdos_profile_names}")

        formatted_profiles = [format_bdos_profile_for_display(entry) for entry in profiles_raw]

        profile_names = [p.get("profile_name") for p in formatted_profiles]

        result['response'] = {
            'rsNetFloodProfileTable': profiles_raw,
            'formatted_profiles': formatted_profiles,
            'summary': {
                'total_entries': len(profiles_raw),
                'unique_profiles': len(set(profile_names)),
                'profile_names': profile_names,
                'filtered': bool(filter_bdos_profile_names),
                'filter_applied': filter_bdos_profile_names if filter_bdos_profile_names else None
            }
        }

        result['debug_info'] = debug_info
        module.exit_json(**result)

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

def main():
    run_module()

if __name__ == '__main__':
    main()
