# plugins/modules/edit_traffic_filter.py
"""
Unified Ansible module to edit Traffic Filter profiles and protections on DefensePro devices.

Supports check mode, logging, error handling, and user-friendly summary output.
User-friendly field names:
 - rsNewTrafficProfileName -> profile_name
 - rsNewTrafficProfileAction -> action
 - rsNewTrafficFilterProfileName -> filter_profile_name
 - rsNewTrafficFilterName -> protection_name
 - rsNewTrafficFilterMatchCriteria -> match_criteria
"""

from ansible.module_utils.basic import AnsibleModule

# Reverse mapping for user-friendly field names (exact keys requested)
REVERSE_FIELD_MAP = {
    "rsNewTrafficProfileName": "profile_name",
    "rsNewTrafficProfileAction": "action",
    "rsNewTrafficFilterProfileName": "filter_profile_name",
    "rsNewTrafficFilterName": "protection_name",
    "rsNewTrafficFilterMatchCriteria": "match_criteria",
    "rsNewTrafficFilterProtocol": "protocol",
    "rsNewTrafficFilterPacketSize": "packet_size",
    "rsNewTrafficFilterTCPFlagsSyn": "tcp_syn",
    "rsNewTrafficFilterTCPFlagsAck": "tcp_ack",
    "rsNewTrafficFilterTCPFlagsRst": "tcp_rst",
    "rsNewTrafficFilterTCPFlagsSynAck": "tcp_synack",
    "rsNewTrafficFilterTCPFlagsFinAck": "tcp_finack",
    "rsNewTrafficFilterTCPFlagsPshAck": "tcp_pshack",
    "rsNewTrafficFilterThresholdPPS": "threshold_pps",
    "rsNewTrafficFilterThresholdBPS": "threshold_bps",
    "rsNewTrafficFilterPacketReport": "packet_report",
    "rsNewTrafficFilterThresholdUsed": "threshold_used",
    "rsNewTrafficFilterAttackTrackingType": "attack_tracking_type",
    "rsNewTrafficFilterCustomProtocol": "custom_protocol"
}

# Enum mappings to human-readable values
REVERSE_ENUM_MAPS = {
    "rsNewTrafficProfileAction": {"1": "enable", "0": "disable"},
    "rsNewTrafficFilterProtocol": {"0": "any", "2": "tcp", "3": "udp"},
    "rsNewTrafficFilterTCPFlagsSyn": {"2": "enable", "1": "disable"},
    "rsNewTrafficFilterTCPFlagsAck": {"2": "enable", "1": "disable"},
    "rsNewTrafficFilterTCPFlagsRst": {"2": "enable", "1": "disable"},
    "rsNewTrafficFilterTCPFlagsSynAck": {"2": "enable", "1": "disable"},
    "rsNewTrafficFilterTCPFlagsFinAck": {"2": "enable", "1": "disable"},
    "rsNewTrafficFilterTCPFlagsPshAck": {"2": "enable", "1": "disable"},
    "rsNewTrafficFilterPacketReport": {"1": "enable", "2": "disable"}
}


def map_api_values_to_user_friendly(api_params):
    """Convert numeric API keys/values to human-friendly names and enums."""
    user_friendly = {}
    for k, v in api_params.items():
        # skip None or empty strings
        if v is None or (isinstance(v, str) and v == ''):
            continue
        # map key name
        name = REVERSE_FIELD_MAP.get(k, k)
        # map enum values if available
        if k in REVERSE_ENUM_MAPS:
            user_friendly[name] = REVERSE_ENUM_MAPS[k].get(str(v), v)
        else:
            user_friendly[name] = v
    return user_friendly


def map_protection_parameters(prot):
    """Map user-friendly protection params to API values (for PUT payload)."""
    TCP_FLAGS_MAP = {'enable': '2', 'disable': '1'}
    PACKET_REPORT_MAP = {'enable': '1', 'disable': '2'}
    PROTOCOL_MAP = {'any': '0', 'tcp': '2', 'udp': '3'}

    protocol = str(prot.get('protocol', 'any')).lower()

    payload = {
        "rsNewTrafficFilterProfileName": prot['profile_name'],
        "rsNewTrafficFilterName": prot['name'],
        "rsNewTrafficFilterMatchCriteria": str(prot.get('match_criteria', '1')),
        "rsNewTrafficFilterProtocol": PROTOCOL_MAP.get(protocol, '0'),
        "rsNewTrafficFilterPacketSize": str(prot.get('packet_size', '')),
        # Only include TCP flags when protocol is tcp or any (device may reject otherwise)
        "rsNewTrafficFilterTCPFlagsSyn": TCP_FLAGS_MAP.get(prot.get('tcp_syn', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsAck": TCP_FLAGS_MAP.get(prot.get('tcp_ack', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsRst": TCP_FLAGS_MAP.get(prot.get('tcp_rst', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsSynAck": TCP_FLAGS_MAP.get(prot.get('tcp_synack', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsFinAck": TCP_FLAGS_MAP.get(prot.get('tcp_finack', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsPshAck": TCP_FLAGS_MAP.get(prot.get('tcp_pshack', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterThresholdPPS": str(prot.get('threshold_pps', '10000')),
        "rsNewTrafficFilterThresholdBPS": str(prot.get('threshold_bps', '0')),
        "rsNewTrafficFilterPacketReport": PACKET_REPORT_MAP.get(prot.get('packet_report', 'enable'), '1'),
        "rsNewTrafficFilterThresholdUsed": str(prot.get('threshold_used', '2')),
        "rsNewTrafficFilterAttackTrackingType": str(prot.get('attack_tracking_type', '0')),
        "rsNewTrafficFilterCustomProtocol": prot.get('custom_protocol', '')
    }

    # Remove keys with None (so they are not sent to API)
    payload = {k: v for k, v in payload.items() if v is not None}
    return payload


def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        traffic_filters=dict(type='dict', required=False, default={})
    )

    result = dict(changed=False, response={}, debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    traffic_filters = module.params['traffic_filters']

    profiles = traffic_filters.get('profiles', [])
    protections = traffic_filters.get('protections', [])

    debug_info = {
        'dp_ip': dp_ip,
        'profiles_count': len(profiles),
        'protections_count': len(protections)
    }

    try:
        from ansible.module_utils.logger import Logger
        from ansible.module_utils.radware_cc import RadwareCC

        log_level = provider.get('log_level', 'disabled')
        logger = Logger(verbosity=log_level)

        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        changes_made = False
        edited_profiles = []
        edited_protections = []
        errors = []

        if module.check_mode:
            preview_ops = {'profiles': profiles, 'protections': protections}
            result.update({'changed': bool(profiles or protections), 'response': {'preview_mode': True, 'planned_operations': preview_ops}})
            module.exit_json(**result)

        # Edit profiles
        for profile in profiles:
            profile_name = profile.get('name')
            if not profile_name:
                err = "Profile name is required"
                errors.append(err)
                logger.error(err)
                continue
            try:
                api_action = "1" if profile.get('params', {}).get('action', 'enable') == 'enable' else "0"
                url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficProfileTable/{profile_name}"
                payload = {"rsNewTrafficProfileName": profile_name, "rsNewTrafficProfileAction": api_action}

                resp = cc._put(url, json=payload)
                resp.raise_for_status()

                # Use mapping that includes profile_name and action keys
                edited_profiles.append({
                    'profile_name': profile_name,
                    'status': 'success',
                    'params_applied': payload,
                    'user_friendly': map_api_values_to_user_friendly(payload)
                })
                changes_made = True
            except Exception as e:
                err_msg = f"Error editing profile {profile_name}: {str(e)}"
                logger.error(err_msg)
                edited_profiles.append({'profile_name': profile_name, 'status': 'failed', 'error': err_msg})
                errors.append(err_msg)

        # Edit protections
        for prot in protections:
            profile_name = prot.get('profile_name')
            protection_name = prot.get('name')
            if not profile_name or not protection_name:
                err = "Protection requires 'profile_name' and 'name'"
                errors.append(err)
                logger.error(err)
                continue
            try:
                api_payload = map_protection_parameters(prot)
                url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficFilterTable/{profile_name}/{protection_name}"

                resp = cc._put(url, json=api_payload)
                resp.raise_for_status()

                edited_protections.append({
                    'profile_name': profile_name,
                    'protection_name': protection_name,
                    'status': 'success',
                    'params_applied': api_payload,
                    'user_friendly': map_api_values_to_user_friendly(api_payload)
                })
                changes_made = True
            except Exception as e:
                err_msg = f"Error editing protection {protection_name} under profile {profile_name}: {str(e)}"
                logger.error(err_msg)
                edited_protections.append({'profile_name': profile_name, 'protection_name': protection_name, 'status': 'failed', 'error': err_msg})
                errors.append(err_msg)

        result.update({
            'changed': changes_made,
            'response': {
                'edited_profiles': edited_profiles,
                'edited_protections': edited_protections,
                'errors': errors,
                'summary': {
                    'successful_profiles': len([p for p in edited_profiles if p['status'] == 'success']),
                    'successful_protections': len([p for p in edited_protections if p['status'] == 'success']),
                    'total_profiles_attempted': len(profiles),
                    'total_protections_attempted': len(protections),
                    'errors_count': len(errors)
                }
            }
        })

    except Exception as e:
        module.fail_json(msg=f"Traffic Filter edit failed: {str(e)}", debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
