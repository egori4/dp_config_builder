# plugins/modules/create_traffic_filter.py
"""
Unified Ansible module to create Traffic Filter profiles and protections on DefensePro devices.

Supports:
- Check mode
- Logging and detailed debug info
- Properly aligned user-friendly summary of created profiles and protections
- Descriptive messages if no TF profiles/protections are configured
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
        "threshold_kbps": prot.get('threshold_kbps', '0'),
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
    # Maps for API conversion
    TCP_FLAGS_MAP = {'enable': '2', 'disable': '1'}
    PACKET_REPORT_MAP = {'enable': '1', 'disable': '2'}
    PROTOCOL_MAP = {'any': '0', 'tcp': '1', 'udp': '2', 'icmp': '3', 'igmp': '4',
                    'sctp': '5', 'icmpv6': '6', 'gre': '7', 'ipinip': '8'}
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
        "rsNewTrafficFilterThresholdBPS": str(prot.get('threshold_kbps', '0')),
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


# --- FIX APPLIED HERE: Reduced Indentation for Cleaner Ansible Output ---

def pretty_profiles(profiles):
    """Nicely formatted string of profiles with aligned parameters."""
    if not profiles:
        return "  No profiles created."
    lines = []
    for prof in profiles:
        # Minimal indentation for profile name
        lines.append(f"  - Profile Name: {prof['profile_name']}")
        
        # Consistent 4 spaces for parameters
        for k, v in prof['user_friendly'].items():
            if k != 'profile_name':
                # Capitalize key for readability
                key = k.replace('_', ' ').capitalize()
                lines.append(f"    - {key}: {v}")
        lines.append("") # Empty line for separation
    return "\n".join(lines)


def pretty_protections(protections):
    """Nicely formatted string of protections with aligned parameters."""
    if not protections:
        return "  No protections created."
    lines = []
    for prot in protections:
        # Minimal indentation for protection name
        lines.append(f"  - Protection Name: {prot['protection_name']} (Profile: {prot['profile_name']})")
        
        # Consistent 4 spaces for parameters
        for k, v in prot['user_friendly'].items():
            if k not in ['profile_name', 'protection_name']:
                # Capitalize key for readability
                key = k.replace('_', ' ').capitalize()
                lines.append(f"    - {key}: {v}")
        lines.append("") # Empty line for separation
    return "\n".join(lines)

# --- End of Output Formatting Functions ---


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

    if not tf_profiles and not tf_protections:
        module.exit_json(
            changed=False,
            msg=f"No Traffic Filter profiles or protections configured for device {dp_ip}."
        )

    try:
        # Conditional import for custom utilities
        try:
            from ansible.module_utils.radware_cc import RadwareCC
            from ansible.module_utils.logger import Logger
        except ImportError:
            module.fail_json(msg="Missing module utilities: radware_cc or logger.")
        
        log_level = provider.get('log_level', 'disabled')
        logger = Logger(verbosity=log_level)
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                         log_level=log_level, logger=logger)

        changes_made = False
        created_profiles = []
        created_protections = []
        errors = []

        if module.check_mode:
            module.exit_json(
                changed=bool(tf_profiles or tf_protections),
                msg=f"CHECK MODE: Traffic Filter operations that would be performed for device {dp_ip}.",
                preview={'profiles': tf_profiles, 'protections': tf_protections}
            )

        # Create Profiles
        for profile in tf_profiles:
            profile_name = profile.get('profile_name')
            if not profile_name:
                errors.append("Profile name missing")
                continue
            try:
                payload = map_profile_parameters(profile)
                url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficProfileTable/{profile_name}"
                
                # Assume _post is equivalent to HTTP POST for creation
                resp = cc._post(url, json=payload)
                resp.raise_for_status()
                
                created_profiles.append({
                    'profile_name': profile_name,
                    'status': 'success',
                    'params_applied': payload,
                    'user_friendly': {"profile_name": profile_name,
                                      "action": "report_only" if payload["rsNewTrafficProfileAction"] == "1" else "block_and_report"}
                })
                changes_made = True
            except Exception as e:
                errors.append(f"Profile {profile_name} creation failed: {str(e)}")

        # Create Protections
        for prot in tf_protections:
            profile_name = prot.get('profile_name')
            protection_name = prot.get('protection_name')
            if not profile_name or not protection_name:
                errors.append("Protection requires 'profile_name' and 'protection_name'")
                continue
            try:
                payload = map_protection_parameters(prot)
                url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficFilterTable/{profile_name}/{protection_name}"
                
                # Assume _post is equivalent to HTTP POST for creation
                resp = cc._post(url, json=payload)
                resp.raise_for_status()
                
                created_protections.append({
                    'profile_name': profile_name,
                    'protection_name': protection_name,
                    'status': 'success',
                    'params_applied': payload,
                    'user_friendly': map_prot_input_to_user_friendly(prot)
                })
                changes_made = True
            except Exception as e:
                errors.append(f"Protection {protection_name} under {profile_name} failed: {str(e)}")

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
                # The corrected output strings are stored here
                'pretty_profiles': pretty_profiles(created_profiles),
                'pretty_protections': pretty_protections(created_protections)
            }
        })

        if errors:
            module.fail_json(msg=f"Traffic Filter creation completed with {len(errors)} error(s).", **result)

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Traffic Filter creation failed: {str(e)}", debug_info=debug_info, **result)


def main():
    run_module()


if __name__ == '__main__':
    main()