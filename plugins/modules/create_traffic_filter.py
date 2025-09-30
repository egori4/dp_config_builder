# plugins/modules/create_traffic_filter.py
"""
Unified Ansible module to create Traffic Filter profiles and protections on DefensePro devices.

Supports check mode, logging, error handling, detailed debug info,
and nicely formatted summary of created profiles and protections.
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
        "match_criteria": prot.get('match_criteria', 'match'),
        "protocol": protocol,
        "threshold_pps": prot.get('threshold_pps', '10000'),
        "threshold_bps": prot.get('threshold_bps', '0'),
        "threshold_unit": prot.get('threshold_unit', 'pps'),
        "attack_tracking_type": prot.get('attack_tracking_type', 'all'),
        "tcp_syn": flag(prot.get('tcp_syn')) if protocol in ['tcp', 'any'] else None,
        "tcp_ack": flag(prot.get('tcp_ack')) if protocol in ['tcp', 'any'] else None,
        "tcp_rst": flag(prot.get('tcp_rst')) if protocol in ['tcp', 'any'] else None,
        "tcp_synack": flag(prot.get('tcp_synack')) if protocol in ['tcp', 'any'] else None,
        "tcp_finack": flag(prot.get('tcp_finack')) if protocol in ['tcp', 'any'] else None,
        "tcp_pshack": flag(prot.get('tcp_pshack')) if protocol in ['tcp', 'any'] else None,
        "packet_report": flag(prot.get('packet_report'))
    }

    # Remove None values
    return {k: v for k, v in user_friendly.items() if v is not None}


def map_protection_parameters(prot):
    """Map user-friendly values to API values for Traffic Filter protections."""
    TCP_FLAGS_MAP = {'enable': '2', 'disable': '1'}
    PACKET_REPORT_MAP = {'enable': '1', 'disable': '2'}
    PROTOCOL_MAP = {
        'any': '0', 'tcp': '1', 'udp': '2', 'icmp': '3', 'igmp': '4',
        'sctp': '5', 'icmpv6': '6', 'gre': '7', 'ipinip': '8'
    }
    THRESHOLD_USED_MAP = {'empty': '0', 'kbps': '1', 'pps': '2'}
    ATTACK_TRACKING_MAP = {'all': '0', 'per_source': '2', 'per_destination': '3',
                           'per_source_and_destination': '4', 'track_returning_traffic': '5'}
    MATCH_CRITERIA_MAP = {'match': '1', 'not-match': '2'}
    STATUS_MAP = {'enable': '1', 'disable': '2'}

    payload = {
        "rsNewTrafficFilterProfileName": prot['profile_name'],
        "rsNewTrafficFilterName": prot['protection_name'],
        "rsNewTrafficFilterMatchCriteria": MATCH_CRITERIA_MAP.get(prot.get('match_criteria', 'match'), '1'),
        "rsNewTrafficFilterProtocol": PROTOCOL_MAP.get(prot.get('protocol', 'any'), '0'),
        "rsNewTrafficFilterTCPFlagsSyn": TCP_FLAGS_MAP.get(prot.get('tcp_syn', 'enable'), '2'),
        "rsNewTrafficFilterTCPFlagsAck": TCP_FLAGS_MAP.get(prot.get('tcp_ack', 'enable'), '2'),
        "rsNewTrafficFilterTCPFlagsRst": TCP_FLAGS_MAP.get(prot.get('tcp_rst', 'enable'), '2'),
        "rsNewTrafficFilterTCPFlagsSynAck": TCP_FLAGS_MAP.get(prot.get('tcp_synack', 'enable'), '2'),
        "rsNewTrafficFilterTCPFlagsFinAck": TCP_FLAGS_MAP.get(prot.get('tcp_finack', 'enable'), '2'),
        "rsNewTrafficFilterTCPFlagsPshAck": TCP_FLAGS_MAP.get(prot.get('tcp_pshack', 'enable'), '2'),
        "rsNewTrafficFilterThresholdPPS": str(prot.get('threshold_pps', '10000')),
        "rsNewTrafficFilterThresholdBPS": str(prot.get('threshold_bps', '0')),
        "rsNewTrafficFilterState": STATUS_MAP.get(prot.get('status', 'enable'), '1'),
        "rsNewTrafficFilterPacketReport": PACKET_REPORT_MAP.get(prot.get('packet_report', 'enable'), '1'),
        "rsNewTrafficFilterThresholdUsed": THRESHOLD_USED_MAP.get(prot.get('threshold_unit', 'pps'), '2'),
        "rsNewTrafficFilterAttackTrackingType": ATTACK_TRACKING_MAP.get(prot.get('attack_tracking_type', 'all'), '0'),
        "rsNewTrafficFilterCustomProtocol": prot.get('custom_protocol', '')
    }
    return payload


def map_profile_parameters(profile):
    """Map profile action to API value."""
    api_action = "1" if profile.get('action', 'report_only') == 'report_only' else "0"
    return {"rsNewTrafficProfileName": profile['profile_name'], "rsNewTrafficProfileAction": api_action}


def pretty_protections(protections):
    """Return a nicely formatted string of protections with aligned parameters."""
    lines = []
    for prot in protections:
        profile_name = prot['profile_name']
        protection_name = prot['protection_name']
        lines.append(f"  - {protection_name} (Profile: {profile_name})")
        lines.append("    Parameters:")
        for k, v in prot['user_friendly'].items():
            if k in ['profile_name', 'protection_name']:
                continue
            lines.append(f"      - {k}: {v}")
        lines.append("")  # Blank line between protections
    return "\n".join(lines)


def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        tf_profiles=dict(type='list', required=False, default=[]),
        tf_protections=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    tf_profiles = module.params['tf_profiles']
    tf_protections = module.params['tf_protections']

    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    debug_info['input'] = {
        'dp_ip': dp_ip,
        'profiles_count': len(tf_profiles),
        'protections_count': len(tf_protections)
    }

    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'],
                       provider['password'], log_level=log_level, logger=logger)

        changes_made = False
        created_profiles = []
        created_protections = []
        errors = []

        if module.check_mode:
            preview_ops = {'profiles': tf_profiles, 'protections': tf_protections}
            result.update({
                'changed': bool(tf_profiles or tf_protections),
                'response': {'preview_mode': True, 'planned_operations': preview_ops}
            })
        else:
            # Create profiles
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
                    resp = cc._post(url, json=payload)
                    resp.raise_for_status()
                    created_profiles.append({
                        'profile_name': profile_name,
                        'status': 'success',
                        'params_applied': payload,
                        'user_friendly': {
                            "profile_name": profile_name,
                            "action": "report_only" if payload["rsNewTrafficProfileAction"]=="1" else "block_and_report"
                        }
                    })
                    changes_made = True
                    logger.info(f"Profile created: {profile_name}")
                    logger.debug(f"Profile payload: {payload}")
                except Exception as e:
                    err = f"Error creating profile {profile_name}: {str(e)}"
                    errors.append(err)
                    logger.error(err)

            # Create protections
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
                    resp = cc._post(url, json=api_payload)
                    resp.raise_for_status()
                    uf_prot = map_prot_input_to_user_friendly(prot)
                    created_protections.append({
                        'profile_name': profile_name,
                        'protection_name': protection_name,
                        'status': 'success',
                        'params_applied': api_payload,
                        'user_friendly': uf_prot
                    })
                    changes_made = True
                    logger.info(f"Protection created: {protection_name} under profile {profile_name}")
                    logger.debug(f"Protection payload: {api_payload}")
                except Exception as e:
                    err = f"Error creating protection {protection_name} under profile {profile_name}: {str(e)}"
                    errors.append(err)
                    logger.error(err)

            result.update({
                'changed': changes_made,
                'response': {
                    'created_profiles': created_profiles,
                    'created_protections': created_protections,
                    'errors': errors,
                    'summary': {
                        'successful_profiles': len(created_profiles),
                        'successful_protections': len(created_protections),
                        'total_profiles_attempted': len(tf_profiles),
                        'total_protections_attempted': len(tf_protections),
                        'errors_count': len(errors)
                    },
                    'pretty_protections': pretty_protections(created_protections)
                }
            })

            debug_info['summary'] = {
                'profiles_created': len(created_profiles),
                'protections_created': len(created_protections),
                'errors_count': len(errors),
                'operations_completed': changes_made
            }

            if errors:
                module.fail_json(msg=f"Traffic Filter creation completed with {len(errors)} error(s).", **result)

    except Exception as e:
        err = f"Traffic Filter creation failed: {str(e)}"
        logger.error(err)
        debug_info['error'] = err
        module.fail_json(msg=err, debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
