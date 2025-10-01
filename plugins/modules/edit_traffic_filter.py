#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unified Ansible module to edit Traffic Filter profiles and protections on DefensePro devices.

Supports check mode, logging, error handling, and debug info for METHOD, URI, status code, response.
Now fails the entire task (red) if any profile or protection edit fails.
"""

from ansible.module_utils.basic import AnsibleModule


def map_prot_input_to_user_friendly(prot):
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

    return {k: v for k, v in user_friendly.items() if v is not None}


def map_protection_parameters(prot):
    TCP_FLAGS_MAP = {'enable': '2', 'disable': '1'}
    PACKET_REPORT_MAP = {'enable': '1', 'disable': '2'}
    PROTOCOL_MAP = {
        'any': '0', 'tcp': '1', 'udp': '2', 'icmp': '3', 'igmp': '4',
        'sctp': '5', 'icmpv6': '6', 'gre': '7', 'ipinip': '8'
    }
    THRESHOLD_USED_MAP = {'empty': '0', 'kbps': '1', 'pps': '2'}
    ATTACK_TRACKING_MAP = {
        'all': '0', 'per_source': '2', 'per_destination': '3',
        'per_source_and_destination': '4', 'track_returning_traffic': '5'
    }
    MATCH_CRITERIA_MAP = {'match': '1', 'not-match': '2'}
    STATUS_MAP = {'enable': '1', 'disable': '2'}

    protocol = str(prot.get('protocol', 'any')).lower()

    payload = {
        "rsNewTrafficFilterProfileName": prot['profile_name'],
        "rsNewTrafficFilterName": prot['protection_name'],
        "rsNewTrafficFilterMatchCriteria": MATCH_CRITERIA_MAP.get(prot.get('match_criteria', 'match'), '1'),
        "rsNewTrafficFilterProtocol": PROTOCOL_MAP.get(protocol, '0'),
        "rsNewTrafficFilterTCPFlagsSyn": TCP_FLAGS_MAP.get(prot.get('tcp_syn', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsAck": TCP_FLAGS_MAP.get(prot.get('tcp_ack', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsRst": TCP_FLAGS_MAP.get(prot.get('tcp_rst', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsSynAck": TCP_FLAGS_MAP.get(prot.get('tcp_synack', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsFinAck": TCP_FLAGS_MAP.get(prot.get('tcp_finack', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterTCPFlagsPshAck": TCP_FLAGS_MAP.get(prot.get('tcp_pshack', 'enable'), '2') if protocol in ['tcp', 'any'] else None,
        "rsNewTrafficFilterThresholdPPS": str(prot.get('threshold_pps', '10000')),
        "rsNewTrafficFilterThresholdBPS": str(prot.get('threshold_kbps', '0')),
        "rsNewTrafficFilterState": STATUS_MAP.get(prot.get('status', 'enable'), '1'),
        "rsNewTrafficFilterPacketReport": PACKET_REPORT_MAP.get(prot.get('packet_report', 'enable'), '1'),
        "rsNewTrafficFilterThresholdUsed": THRESHOLD_USED_MAP.get(prot.get('threshold_unit', 'pps'), '2'),
        "rsNewTrafficFilterAttackTrackingType": ATTACK_TRACKING_MAP.get(prot.get('attack_tracking_type', 'all'), '0'),
        "rsNewTrafficFilterCustomProtocol": prot.get('custom_protocol', '')
    }

    return {k: v for k, v in payload.items() if v is not None}


def map_profile_parameters(profile):
    API_ACTION_MAP = {'report_only': '0', 'block_and_report': '1'}
    api_action = API_ACTION_MAP.get(profile.get('action', 'report_only'), '1')
    return {"rsNewTrafficProfileName": profile['profile_name'], "rsNewTrafficProfileAction": api_action}


def pretty_protections(protections):
    lines = []
    for prot in protections:
        profile_name = prot.get('profile_name', 'N/A')
        protection_name = prot.get('protection_name', 'N/A')
        lines.append(f"  - {protection_name} (Profile: {profile_name})")
        if prot.get('user_friendly'):
            lines.append("    Parameters:")
            for k, v in prot['user_friendly'].items():
                if k in ['profile_name', 'protection_name']:
                    continue
                lines.append(f"      - {k}: {v}")
        if prot.get('error'):
            lines.append(f"    Error: {prot['error']}")
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
    debug_info = {
        'dp_ip': dp_ip,
        'profiles_count': len(tf_profiles),
        'protections_count': len(tf_protections)
    }

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)
        changes_made = False
        edited_profiles = []
        edited_protections = []

        if module.check_mode:
            preview_ops = {'profiles': tf_profiles, 'protections': tf_protections}
            result.update({
                'changed': bool(tf_profiles or tf_protections),
                'response': {'preview_mode': True, 'planned_operations': preview_ops}
            })
            module.exit_json(**result)

        # Edit Profiles
        for profile in tf_profiles:
            profile_name = profile.get('profile_name')
            if not profile_name:
                module.fail_json(msg="Profile name is required", debug_info=debug_info)
            payload = map_profile_parameters(profile)
            url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficProfileTable/{profile_name}"
            logger.debug(f"PUT {url} payload={payload}")
            try:
                resp = cc._put(url, json=payload)
                logger.debug(f"Response: code={resp.status_code}, body={resp.text}")
                resp.raise_for_status()
                edited_profiles.append({
                    'profile_name': profile_name,
                    'status': 'success',
                    'params_applied': payload,
                    'user_friendly': {"profile_name": profile_name, "action": profile.get('action', 'report_only')}
                })
                changes_made = True
            except Exception as e:
                module.fail_json(
                    msg=f"Error editing profile {profile_name}: {str(e)}",
                    debug_info={'method': 'PUT', 'uri': url, 'profile': profile_name, 'exception': str(e)}
                )

        # Edit Protections
        for prot in tf_protections:
            profile_name = prot.get('profile_name')
            protection_name = prot.get('protection_name')
            if not profile_name or not protection_name:
                module.fail_json(msg="Protection requires 'profile_name' and 'protection_name'",
                                 debug_info=debug_info)
            api_payload = map_protection_parameters(prot)
            url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficFilterTable/{profile_name}/{protection_name}"
            logger.debug(f"PUT {url} payload={api_payload}")
            try:
                resp = cc._put(url, json=api_payload)
                logger.debug(f"Response: code={resp.status_code}, body={resp.text}")
                resp.raise_for_status()
                uf_prot = map_prot_input_to_user_friendly(prot)
                edited_protections.append({
                    'profile_name': profile_name,
                    'protection_name': protection_name,
                    'status': 'success',
                    'params_applied': api_payload,
                    'user_friendly': uf_prot
                })
                changes_made = True
            except Exception as e:
                module.fail_json(
                    msg=f"Error editing protection {protection_name} under profile {profile_name}: {str(e)}",
                    debug_info={'method': 'PUT', 'uri': url, 'profile': profile_name, 'protection': protection_name, 'exception': str(e)}
                )

        result.update({
            'changed': changes_made,
            'response': {
                'edited_profiles': edited_profiles,
                'edited_protections': edited_protections,
                'pretty_protections': pretty_protections(edited_protections)
            }
        })

    except Exception as e:
        module.fail_json(msg=f"Traffic Filter edit failed: {str(e)}", debug_info=debug_info)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
