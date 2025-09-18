# plugins/modules/get_oos_profile.py
"""
Ansible module to fetch DefensePro OOS profiles via CyberController API.

- Fetches all Stateful profiles from a DefensePro device.
- Maps API response values back to user-friendly keys (reverse of create/edit logic).
- Returns structured response with raw, formatted, and summary data (aligned with get_bdos_profile.py).
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC

def format_oos_profile_for_display(raw_profile_data):
    """
    Convert raw OOS profile API data to user-friendly format.
    """
    FIELD_MAP = {
        "rsSTATFULProfileactThreshold": "act_threshold",
        "rsSTATFULProfiletermThreshold": "term_threshold",
        "rsSTATFULProfilesynAckAllow": "syn_ack_allow",
        "rsSTATFULProfilePacketReportStatus": "packet_report",
        "rsSTATFULProfileAction": "action",
        "rsSTATFULProfileRisk": "risk",
        "rsSTATFULProfileEnableIdleState": "idle_state",
        "rsSTATFULProfileIdleStateBandwidthThreshold": "idle_state_bandwidth_threshold",
        "rsSTATFULProfileIdleStateTimer": "idle_state_timer"
    }

    VALUE_MAPS = {
        "syn_ack_allow": {"1": "enable", "2": "disable"},
        "packet_report": {"1": "enable", "2": "disable"},
        "action": {"0": "report_only", "1": "block_and_report"},
        "risk": {"info": "0", "low": "1", "medium": "2", "high": "3"},
        "idle_state": {"1": "enable", "2": "disable"}
    }

    formatted = {}
    for api_field, user_field in FIELD_MAP.items():
        value = raw_profile_data.get(api_field)
        if value is None:
            continue

        if user_field in VALUE_MAPS and str(value) in VALUE_MAPS[user_field]:
            formatted[user_field] = VALUE_MAPS[user_field][str(value)]
        else:
            formatted[user_field] = value

    return formatted

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        filter_oos_profile_names=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    filter_oos_profile_names = module.params['filter_oos_profile_names']

    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                   log_level=log_level, logger=logger)

    try:
        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsStatefulProfileTable"
        logger.info(f"Fetching OOS profiles from device {dp_ip}")
        resp = cc._get(url)
        data = resp.json()

        profiles_raw = data.get('rsStatefulProfileTable', [])
        debug_info['profiles_raw_count'] = len(profiles_raw)

        # Apply filter if provided
        if filter_oos_profile_names:
            profiles_raw = [p for p in profiles_raw if p.get('rsSTATFULProfileName') in filter_oos_profile_names]
            logger.info(f"Filtered profiles to: {filter_oos_profile_names}")

        profiles_summary = {}
        formatted_profiles = {}

        for entry in profiles_raw:
            profile_name = entry.get('rsSTATFULProfileName', '')
            if not profile_name:
                continue

            if profile_name not in profiles_summary:
                profiles_summary[profile_name] = []
                formatted_profiles[profile_name] = []

            profiles_summary[profile_name].append(entry)
            formatted_entry = format_oos_profile_for_display(entry)
            formatted_profiles[profile_name].append(formatted_entry)

        result['response'] = {
            'rsStatefulProfileTable': profiles_raw,
            'formatted_profiles': formatted_profiles,
            'summary': {
                'total_entries': len(profiles_raw),
                'unique_profiles': len(profiles_summary),
                'profile_names': list(profiles_summary.keys()),
                'filtered': bool(filter_oos_profile_names),
                'filter_applied': filter_oos_profile_names if filter_oos_profile_names else None
            },
            'profiles_breakdown': profiles_summary
        }

        debug_info['summary'] = {
            'total_entries_retrieved': len(profiles_raw),
            'unique_profiles_found': len(profiles_summary),
            'filter_applied': bool(filter_oos_profile_names),
            'profile_names_found': list(profiles_summary.keys())
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
