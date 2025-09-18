# plugins/modules/get_oos_profile.py
"""
Ansible module to fetch DefensePro OOS profiles via CyberController API.

- Fetches all Stateful profiles from a DefensePro device.
- Maps API response values back to user-friendly keys (reverse of create/edit logic).
- Returns a nested response suitable for playbooks or reporting.
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        filter_oos_profile_names=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, oos_profiles=[], debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    filter_oos_profile_names = module.params['filter_oos_profile_names']

    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'], log_level=log_level, logger=logger)

    debug_info = {}

    # Reverse mappings (API value -> user-friendly)
    ENUM_MAPS = {
        "syn_ack_allow": {"1": "enable", "2": "disable"},
        "packet_report": {"1": "enable", "2": "disable"},
        "action": {"0": "report_only", "1": "block_and_report"},
        "risk": {"1": "low", "2": "medium", "3": "high"},
        "idle_state": {"1": "enable", "2": "disable"}
    }

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

    try:
        # Fetch all OOS profiles
        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsStatefulProfileTable"
        logger.info(f"Fetching OOS profiles from device {dp_ip}")
        resp = cc._get(url)
        profiles_raw = resp.json().get('rsStatefulProfileTable', [])
        debug_info['profiles_raw_count'] = len(profiles_raw)

        oos_profiles = []
        for profile in profiles_raw:
            profile_name = profile.get('rsSTATFULProfileName')
            mapped_params = {}
            for api_key, user_key in FIELD_MAP.items():
                value = profile.get(api_key)
                if value is None:
                    continue
                # Reverse mapping for enums
                for enum_key, mapping in ENUM_MAPS.items():
                    if user_key == enum_key:
                        value = mapping.get(str(value), value)
                mapped_params[user_key] = value
            oos_profiles.append({
                'name': profile_name,
                'params': mapped_params
            })

        # Apply filter if requested
        if filter_oos_profile_names:
            filtered_profiles = [p for p in oos_profiles if p['name'] in filter_oos_profile_names]
            result['oos_profiles'] = filtered_profiles
            debug_info['filter_applied'] = True
            debug_info['filter_oos_profile_names'] = filter_oos_profile_names
            debug_info['filtered_count'] = len(filtered_profiles)
            debug_info['total_count'] = len(oos_profiles)
        else:
            result['oos_profiles'] = oos_profiles
            debug_info['filter_applied'] = False
            debug_info['total_count'] = len(oos_profiles)

        result['debug_info'] = debug_info
        module.exit_json(**result)

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
