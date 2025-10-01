# plugins/modules/edit_traffic_filter.py
"""
Unified Ansible module to edit Traffic Filter profiles and protections on DefensePro devices.

Supports:
- Check mode
- Logging (info/debug/error)
- Pretty-print summaries
- Proper error handling with fail_json if errors exist
- Fully aligned with create_traffic_filter.py
"""

from ansible.module_utils.basic import AnsibleModule


def map_prot_input_to_user_friendly(prot):
    """Convert protection input to human-readable values."""
    protocol = str(prot.get('protocol', 'any')).lower()

    def flag(val):
        if val is None:
            return None
        return "enable" if str(val).lower() in ['enabled', 'enable', '2'] else "disable"

    user_friendly = {
        "profile_name": prot.get('profile_name'),
        "protection_name": prot.get('protection_name'),
        "status": prot.get('status', 'enable'),
        "match_criteria": prot.get('match_criteria', 'match'),
        "protocol": protocol,
        "tcp_syn": flag(prot.get('tcp_syn')) if protocol in ['tcp', 'any'] else None,
        "tcp_ack": flag(prot.get('tcp_ack')) if protocol in ['tcp', 'any'] else None,
        "tcp_rst": flag(prot.get('tcp_rst')) if protocol in ['tcp', 'any'] else None,
        "tcp_synack": flag(prot.get('tcp_synack')) if protocol in ['tcp', 'any'] else None,
        "tcp_finack": flag(prot.get('tcp_finack')) if protocol in ['tcp', 'any'] else None,
        "tcp_pshack": flag(prot.get('tcp_pshack')) if protocol in ['tcp', 'any'] else None,
        "threshold_pps": prot.get('threshold_pps', '10000'),
        "threshold_bps": prot.get('threshold_bps', '0'),
        "packet_report": flag(prot.get('packet_report')),
        "threshold_unit": prot.get('threshold_unit', 'pps'),
        "attack_tracking_type": prot.get('attack_tracking_type', '')
    }

    return {k: v for k, v in user_friendly.items() if v is not None}


def map_protection_parameters(prot):
    """Map user-friendly protection params to API values (for PUT payload)."""
    TCP_FLAGS_MAP = {'enable': '1', 'disable': '2'}
    PACKET_REPORT_MAP = {'enable': '1', 'disable': '2'}
    PROTOCOL_MAP = {
        'any': '0', 'tcp': '1', 'udp': '2', 'icmp': '3', 'igmp': '4',
        'sctp': '5', 'icmpv6': '6', 'gre': '7', 'ipinip': '8'
    }
    THRESHOLD_USED_MAP = {'empty': '0', 'kbps': '1', 'pps': '2'}
    ATTACK_TRACKING_MAP = {
        'all': '0', 'per_source': '2', 'per_destination': '3',
        'per_source_and_destination': '4', 'track_returning_traffic': '5', 'drop': '0'
    }
    MATCH_CRITERIA_MAP = {'match': '1', 'not-match': '2'}
    STATUS_MAP = {'enable': '1', 'disable': '2'}

    protocol = str(prot.get('protocol', 'any')).lower()

    payload = {
        "rsNewTrafficFilterProfileName": prot['profile_name'],
        "rsNewTrafficFilterName": prot['protection_name'],
        "rsNewTrafficFilterMatchCriteria": MATCH_CRITERIA_MAP.get(prot.get('match_criteria', 'match'), '1'),
        "rsNewTrafficFilterProtocol": PROTOCOL_MAP.get(protocol, '0'),
        "rsNewTrafficFilterTCPFlagsSyn": TCP_FLAGS_MAP.get(prot.get('tcp_syn', 'enable'), '1') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsAck": TCP_FLAGS_MAP.get(prot.get('tcp_ack', 'enable'), '1') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsRst": TCP_FLAGS_MAP.get(prot.get('tcp_rst', 'enable'), '1') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsSynAck": TCP_FLAGS_MAP.get(prot.get('tcp_synack', 'enable'), '1') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsFinAck": TCP_FLAGS_MAP.get(prot.get('tcp_finack', 'enable'), '1') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsPshAck": TCP_FLAGS_MAP.get(prot.get('tcp_pshack', 'enable'), '1') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterThresholdPPS": str(prot.get('threshold_pps', '10000')),
        "rsNewTrafficFilterThresholdBPS": str(prot.get('threshold_bps', '0')),
        "rsNewTrafficFilterState": STATUS_MAP.get(prot.get('status', 'enable'), '1'),
        "rsNewTrafficFilterPacketReport": PACKET_REPORT_MAP.get(prot.get('packet_report', 'enable'), '1'),
        "rsNewTrafficFilterThresholdUsed": THRESHOLD_USED_MAP.get(prot.get('threshold_unit', 'pps'), '2'),
        "rsNewTrafficFilterAttackTrackingType": ATTACK_TRACKING_MAP.get(prot.get('attack_tracking_type', 'all'), '0'),
        "rsNewTrafficFilterCustomProtocol": prot.get('custom_protocol', '')
    }

    return {k: v for k, v in payload.items() if v is not None}


def map_profile_parameters(profile):
    """Map profile action to API value."""
    API_ACTION_MAP = {'report_only': '1', 'block_and_report': '0'}
    api_action = API_ACTION_MAP.get(profile.get('action', 'report_only'), '1')
    return {"rsNewTrafficProfileName": profile['profile_name'], "rsNewTrafficProfileAction": api_action}


def pretty_profiles(profiles):
    if not profiles:
        return "  No profiles edited."
    lines = []
    for prof in profiles:
        lines.append(f"  - Profile Name: {prof['profile_name']} ({prof['status']})")
        for k, v in prof['user_friendly'].items():
            if k != 'profile_name':
                key = k.replace('_', ' ').capitalize()
                lines.append(f"    - {key}: {v}")
        lines.append("")
    return "\n".join(lines)


def pretty_protections(protections):
    if not protections:
        return "  No protections edited."
    lines = []
    for prot in protections:
        lines.append(f"  - Protection Name: {prot['protection_name']} (Profile: {prot['profile_name']}, {prot['status']})")
        for k, v in prot['user_friendly'].items():
            if k not in ['profile_name', 'protection_name']:
                key = k.replace('_', ' ').capitalize()
                lines.append(f"    - {key}: {v}")
        lines.append("")
    return "\n".join(lines)


def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        tf_profiles=dict(type='list', required=False, default=[]),
        tf_protections=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={}, debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    tf_profiles = module.params['tf_profiles']
    tf_protections = module.params['tf_protections']

    from ansible.module_utils.logger import Logger
    from ansible.module_utils.radware_cc import RadwareCC

    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    debug_info = {'dp_ip': dp_ip, 'profiles_count': len(tf_profiles), 'protections_count': len(tf_protections)}

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'], log_level=log_level, logger=logger)
        changes_made = False
        edited_profiles = []
        edited_protections = []
        errors = []

        if module.check_mode:
            module.exit_json(
                changed=bool(tf_profiles or tf_protections),
                msg=f"CHECK MODE: Traffic Filter edit operations that would be performed for device {dp_ip}.",
                preview={'profiles': tf_profiles, 'protections': tf_protections}
            )

        # Edit profiles
        for profile in tf_profiles:
            profile_name = profile.get('profile_name')
            if not profile_name:
                err = "Profile name is required"
                errors.append(err)
                logger.error(err)
                continue
            try:
                payload = map_profile_parameters(profile)
                url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficProfileTable/{profile_name}"

                logger.info(f"Editing profile: {profile_name} on {dp_ip}")
                logger.debug(f"Request URL: {url}")
                logger.debug(f"Request payload: {payload}")

                resp = cc._put(url, json=payload)
                resp.raise_for_status()

                edited_profiles.append({
                    'profile_name': profile_name,
                    'status': 'success',
                    'params_applied': payload,
                    'user_friendly': {"profile_name": profile_name, "action": profile.get('action', 'report_only')}
                })
                changes_made = True
                logger.info(f"Successfully edited profile: {profile_name}")
            except Exception as e:
                err_msg = f"Error editing profile {profile_name}: {str(e)}"
                logger.error(err_msg)
                edited_profiles.append({'profile_name': profile_name, 'status': 'failed', 'error': err_msg})
                errors.append(err_msg)

        # Edit protections
        for prot in tf_protections:
            profile_name = prot.get('profile_name')
            protection_name = prot.get('protection_name')
            if not profile_name or not protection_name:
                err = "Protection requires 'profile_name' and 'protection_name'"
                errors.append(err)
                logger.error(err)
                continue
            try:
                api_payload = map_protection_parameters(prot)
                url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficFilterTable/{profile_name}/{protection_name}"

                logger.info(f"Editing protection: {protection_name} under profile {profile_name} on {dp_ip}")
                logger.debug(f"Request URL: {url}")
                logger.debug(f"Request payload: {api_payload}")

                resp = cc._put(url, json=api_payload)
                resp.raise_for_status()

                edited_protections.append({
                    'profile_name': profile_name,
                    'protection_name': protection_name,
                    'status': 'success',
                    'params_applied': api_payload,
                    'user_friendly': map_prot_input_to_user_friendly(prot)
                })
                changes_made = True
                logger.info(f"Successfully edited protection: {protection_name} under profile {profile_name}")
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
                    'total_profiles_attempted': len(tf_profiles),
                    'total_protections_attempted': len(tf_protections),
                    'errors_count': len(errors)
                },
                'pretty_profiles': pretty_profiles(edited_profiles),
                'pretty_protections': pretty_protections(edited_protections)
            },
            'debug_info': debug_info
        })

        if errors:
            module.fail_json(msg=f"Traffic Filter edit completed with {len(errors)} error(s).", **result)

        module.exit_json(**result)

    except Exception as e:
        error_msg = f"Traffic Filter edit failed: {str(e)}"
        logger.error(error_msg)
        debug_info['error'] = error_msg
        module.fail_json(msg=error_msg, debug_info=debug_info, **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
