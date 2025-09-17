# plugins/modules/get_bdos_profile.py
"""
Ansible module to fetch DefensePro BDoS profiles via Radware CyberController API.

This module handles retrieval of BDoS Flood profiles with filtering support,
following the unified pattern from other enhanced modules.
"""

from ansible.module_utils.basic import AnsibleModule

def format_bdos_profile_for_display(raw_profile_data):
    """
    Convert raw BDoS profile API data to user-friendly format using the same
    field mappings as create_bdos_profile.py for consistency.
    """
    
    # Reverse mappings from API fields to user-friendly names
    FIELD_MAP_REVERSE = {
        "rsIDSNewRulesName": "profile_name",
        "rsIDSNewRulesState": "status",
        "rsIDSNewRulesAction": "action",
        "rsIDSNewRulesSource": "source",
        "rsIDSNewRulesDestination": "destination", 
        "rsIDSNewRulesDirection": "direction",
        "rsIDSNewRulesPortmask": "portmask",
        "rsIDSNewRulesPriority": "priority",
        "rsIDSNewRulesVlanTagGroup": "vlan_tag_group",
        "rsIDSNewRulesPacketReportingStatus": "packet_reporting_status",
        "rsIDSNewRulesPacketReportingEnforcement": "packet_reporting_enforcement",
        "rsIDSNewRulesPacketTraceStatus": "packet_trace_status",
        "rsIDSNewRulesPacketTraceEnforcement": "packet_trace_enforcement",
        
        # Protection profiles
        "rsIDSNewRulesProfileNetflood": "netflood_profile",
        "rsIDSNewRulesProfileAppsec": "appsec_profile", 
        "rsIDSNewRulesProfileConlmt": "connection_limit_profile",
        "rsIDSNewRulesProfileStateful": "stateful_profile",
        "rsIDSNewRulesProfileScanning": "scanning_profile",
        "rsIDSNewRulesProfileSynprotection": "syn_protection_profile",
        "rsIDSNewRulesProfileDNS": "dns_profile",
        "rsIDSNewRulesProfileHttpsflood": "https_flood_profile",
        "rsIDSNewRulesProfileErtAttackersFeed": "ert_attackers_feed_profile",
        "rsIDSNewRulesProfileTrafficFilters": "traffic_filters_profile",
        "rsIDSNewRulesProfileGeoFeed": "geo_feed_profile",
        "rsIDSNewRulesProfileQdos": "qdos_profile",
        
        # CDN settings
        "rsIDSNewRulesCdnAction": "cdn_action",
        "rsIDSNewRulesCdnHandling": "cdn_handling",
        "rsIDSNewRulesCdnHandlingHttps": "cdn_handling_https",
        "rsIDSNewRulesCdnHandlingSig": "cdn_handling_sig",
        "rsIDSNewRulesCdnHandlingSyn": "cdn_handling_syn",
        "rsIDSNewRulesCdnHandlingTF": "cdn_handling_tf",
        "rsIDSNewRulesCdnTrueIpCustomHdr": "cdn_true_ip_custom_header",
        "rsIDSNewRulesCdnHdrNotFoundFallback": "cdn_header_not_found_fallback",
        "rsIDSNewRulesCdnTrueClientIpHdr": "cdn_true_client_ip_header",
        "rsIDSNewRulesCdnXForwardedForHdr": "cdn_x_forwarded_for_header",
        "rsIDSNewRulesCdnForwardedHdr": "cdn_forwarded_header",
        
        # Other fields
        "rsIDSNewRulesInstanceId": "instance_id",
        "rsIDSNewRulesMPLSRDGroup": "mpls_rd_group",
        "rsIDSQuarantineStatusInPolicy": "quarantine_status",
        "rsIDSServiceName": "service_name",
        "rsIDSNewRulesDnsSDAllowListEnforce": "dns_sd_allow_list_enforce"
    }
    
    # Value mappings to human-readable format
    VALUE_MAPS = {
        "status": {"1": "enabled", "2": "disabled"},
        "action": {"0": "report_only", "1": "block_and_report"},
        "direction": {"1": "inbound", "2": "outbound", "3": "bidirectional"},
        "packet_reporting_status": {"1": "enabled", "2": "disabled"},
        "packet_reporting_enforcement": {"1": "enabled", "2": "disabled"},
        "packet_trace_status": {"1": "enabled", "2": "disabled"},
        "packet_trace_enforcement": {"1": "enabled", "2": "disabled"},
        "cdn_action": {"1": "enabled", "2": "disabled"},
        "cdn_handling": {"1": "enabled", "2": "disabled"},
        "cdn_handling_https": {"1": "enabled", "2": "disabled"},
        "cdn_handling_sig": {"1": "enabled", "2": "disabled"},
        "cdn_handling_syn": {"1": "enabled", "2": "disabled"},
        "cdn_handling_tf": {"1": "enabled", "2": "disabled"},
        "cdn_header_not_found_fallback": {"1": "enabled", "2": "disabled"},
        "cdn_true_client_ip_header": {"1": "enabled", "2": "disabled"},
        "cdn_x_forwarded_for_header": {"1": "enabled", "2": "disabled"},
        "cdn_forwarded_header": {"1": "enabled", "2": "disabled"},
        "quarantine_status": {"1": "enabled", "2": "disabled"},
        "dns_sd_allow_list_enforce": {"1": "enabled", "2": "disabled"}
    }
    
    formatted = {}
    
    for api_field, raw_value in raw_profile_data.items():
        # Skip empty or null values
        if not raw_value or raw_value in ["", "OBSOLETE"]:
            continue
            
        # Get user-friendly field name
        user_field = FIELD_MAP_REVERSE.get(api_field, api_field)
        
        # Apply value mapping if available
        if user_field in VALUE_MAPS and str(raw_value) in VALUE_MAPS[user_field]:
            formatted[user_field] = VALUE_MAPS[user_field][str(raw_value)]
        else:
            formatted[user_field] = raw_value
    
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
    
    # Extract provider and setup logging
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    filter_bdos_profile_names = module.params['filter_bdos_profile_names']
    
    log_level = provider.get('log_level', 'disabled')
    
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    debug_info['input'] = {
        'dp_ip': dp_ip,
        'filter_bdos_profile_names': filter_bdos_profile_names,
        'filter_count': len(filter_bdos_profile_names) if filter_bdos_profile_names else 0
    }
    
    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        # Get BDoS profiles from device
        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable"
        
        logger.info(f"Getting BDoS profile info for device {dp_ip}")
        if filter_bdos_profile_names:
            logger.info(f"Filtering for profile names: {filter_bdos_profile_names}")
        else:
            logger.info("Getting all BDoS profiles (no filter)")
        
        logger.debug(f"Request URL: {url}")
        
        resp = cc._get(url)
        data = resp.json()
        
        logger.debug(f"Response status: {resp.status_code}")
        logger.debug(f"Raw response: {data}")
        
        # Process and filter the response
        bdos_table = data.get('rsIDSNewRulesTable', [])
        
        if filter_bdos_profile_names:
            # Filter by profile names
            filtered_table = []
            for entry in bdos_table:
                profile_name = entry.get('rsIDSNewRulesName', '')
                if profile_name in filter_bdos_profile_names:
                    filtered_table.append(entry)
            
            logger.info(f"Filtered {len(bdos_table)} entries to {len(filtered_table)} matching profile names")
            bdos_table = filtered_table
        else:
            logger.info(f"Retrieved {len(bdos_table)} BDoS profile entries")
        
        # Organize data by profile for better structure
        profiles_summary = {}
        formatted_profiles = {}
        
        for entry in bdos_table:
            profile_name = entry.get('rsIDSNewRulesName', '')
            if profile_name not in profiles_summary:
                profiles_summary[profile_name] = []
                formatted_profiles[profile_name] = []
            
            profiles_summary[profile_name].append(entry)
            # Add user-friendly formatted version
            formatted_entry = format_bdos_profile_for_display(entry)
            formatted_profiles[profile_name].append(formatted_entry)
        
        result['response'] = {
            'rsIDSNewRulesTable': bdos_table,
            'formatted_profiles': formatted_profiles,
            'summary': {
                'total_entries': len(bdos_table),
                'unique_profiles': len(profiles_summary),
                'profile_names': list(profiles_summary.keys()),
                'filtered': bool(filter_bdos_profile_names),
                'filter_applied': filter_bdos_profile_names if filter_bdos_profile_names else None
            },
            'profiles_breakdown': profiles_summary
        }
        
        debug_info['summary'] = {
            'total_entries_retrieved': len(bdos_table),
            'unique_profiles_found': len(profiles_summary),
            'filter_applied': bool(filter_bdos_profile_names),
            'profile_names_found': list(profiles_summary.keys())
        }
        
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)
    
    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
