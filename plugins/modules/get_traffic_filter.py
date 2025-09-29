"""
Ansible module to fetch DefensePro Traffic Filter profiles, associated protections, and protection settings.

- Fetches all profiles and protections from DefensePro via CyberController API
- Combines and maps data to a nested structure: profiles -> protections
- Returns user-friendly nested response with enabled/disabled mapping
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        filter_tf_profile_names=dict(type='list', required=False, default=[])
    )
    result = dict(changed=False, profiles=[], debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    filter_tf_profile_names = module.params['filter_tf_profile_names']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'], log_level=log_level, logger=logger)
    debug_info = {}

    # Reverse mappings (API value -> user-friendly)
    ENABLED_DISABLED_MAP = {'1': 'enabled', '2': 'disabled'}
    PROTOCOL_MAP = {'0': 'any', '2': 'tcp', '3': 'udp'}
    ACTION_MAP = {'0': 'report_only', '1': 'report_only', '10': 'drop'}

    try:
        # 1. Get all profiles
        profile_path = f"/mgmt/device/byip/{dp_ip}/config/rsNewTrafficProfileTable"
        profile_url = f"https://{provider['cc_ip']}{profile_path}"
        logger.info(f"Fetching traffic filter profiles from {dp_ip}")
        resp = cc._get(profile_url)
        profiles_raw = resp.json().get('rsNewTrafficProfileTable', [])
        debug_info['profiles_raw_count'] = len(profiles_raw)

        # 2. Get all protections
        prot_path = f"/mgmt/device/byip/{dp_ip}/config/rsNewTrafficFilterTable"
        prot_url = f"https://{provider['cc_ip']}{prot_path}"
        logger.info(f"Fetching traffic filter protections from {dp_ip}")
        resp = cc._get(prot_url)
        protections_raw = resp.json().get('rsNewTrafficFilterTable', [])
        debug_info['protections_raw_count'] = len(protections_raw)

        # 3. Build nested profile structure
        profiles = {}
        for profile in profiles_raw:
            prof_name = profile['rsNewTrafficProfileName']
            if prof_name not in profiles:
                profiles[prof_name] = {
                    'profile_name': prof_name,
                    'num_of_rules': int(profile.get('rsNewTrafficProfileNumOfRules', 0)),
                    'action': ACTION_MAP.get(profile.get('rsNewTrafficProfileAction', ''), profile.get('rsNewTrafficProfileAction', '')),
                    'protections': []
                }

        # 4. Add protections to profiles
        for prot in protections_raw:
            prof_name = prot.get('rsNewTrafficFilterProfileName')
            if prof_name in profiles:
                prot_entry = {
                    'protection_name': prot.get('rsNewTrafficFilterName'),
                    'protection_id': prot.get('rsNewTrafficFilterID'),
                    'state': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterState', ''), prot.get('rsNewTrafficFilterState', '')),
                    'priority': prot.get('rsNewTrafficFilterPriority', '0'),
                    'protocol': PROTOCOL_MAP.get(prot.get('rsNewTrafficFilterProtocol', ''), prot.get('rsNewTrafficFilterProtocol', '')),
                    'threshold_pps': prot.get('rsNewTrafficFilterThresholdPPS', '0'),
                    'threshold_bps': prot.get('rsNewTrafficFilterThresholdBPS', '0'),
                    'packet_report': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterPacketReport', ''), prot.get('rsNewTrafficFilterPacketReport', '')),
                    'vlan': prot.get('rsNewTrafficFilterVLAN', 'Any'),

                    # TCP Flags mapped
                    'tcp_syn': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterTCPFlagsSyn', ''), prot.get('rsNewTrafficFilterTCPFlagsSyn', '')),
                    'tcp_ack': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterTCPFlagsAck', ''), prot.get('rsNewTrafficFilterTCPFlagsAck', '')),
                    'tcp_rst': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterTCPFlagsRst', ''), prot.get('rsNewTrafficFilterTCPFlagsRst', '')),
                    'tcp_synack': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterTCPFlagsSynAck', ''), prot.get('rsNewTrafficFilterTCPFlagsSynAck', '')),
                    'tcp_finack': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterTCPFlagsFinAck', ''), prot.get('rsNewTrafficFilterTCPFlagsFinAck', '')),
                    'tcp_pshack': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterTCPFlagsPshAck', ''), prot.get('rsNewTrafficFilterTCPFlagsPshAck', '')),

                    # DNS Types mapped
                    'dns_type_a': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterDnsTypeA', ''), prot.get('rsNewTrafficFilterDnsTypeA', '')),
                    'dns_type_aaaa': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterDnsTypeAAAA', ''), prot.get('rsNewTrafficFilterDnsTypeAAAA', '')),
                    'dns_type_mx': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterDnsTypeMX', ''), prot.get('rsNewTrafficFilterDnsTypeMX', '')),
                    'dns_type_ptr': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterDnsTypePTR', ''), prot.get('rsNewTrafficFilterDnsTypePTR', '')),
                    'dns_type_cname': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterDnsTypeCNAME', ''), prot.get('rsNewTrafficFilterDnsTypeCNAME', '')),
                    'dns_type_ns': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterDnsTypeNS', ''), prot.get('rsNewTrafficFilterDnsTypeNS', '')),
                    'dns_type_txt': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterDnsTypeTXT', ''), prot.get('rsNewTrafficFilterDnsTypeTXT', '')),
                    'dns_type_any': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterDnsTypeANY', ''), prot.get('rsNewTrafficFilterDnsTypeANY', '')),
                    'dns_type_soa': ENABLED_DISABLED_MAP.get(prot.get('rsNewTrafficFilterDnsTypeSOA', ''), prot.get('rsNewTrafficFilterDnsTypeSOA', '')),

                    'src_network': prot.get('rsNewTrafficFilterSrcNetwork', ''),
                    'src_port': prot.get('rsNewTrafficFilterSrcPort', ''),
                    'dst_network': prot.get('rsNewTrafficFilterDstNetwork', ''),
                    'dst_port': prot.get('rsNewTrafficFilterDstPort', '')
                }
                profiles[prof_name]['protections'].append(prot_entry)

        # Apply filtering if filter_tf_profile_names is provided
        all_profiles = list(profiles.values())
        if filter_tf_profile_names:
            filtered_profiles = [p for p in all_profiles if p['profile_name'] in filter_tf_profile_names]
            result['profiles'] = filtered_profiles
            debug_info['filter_applied'] = True
            debug_info['filter_tf_profile_names'] = filter_tf_profile_names
        else:
            result['profiles'] = all_profiles
            debug_info['filter_applied'] = False

        result['debug_info'] = debug_info
        module.exit_json(**result)

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

def main():
    run_module()

if __name__ == '__main__':
    main()
