"""
Unified Ansible module to manage DefensePro Traffic Filter profiles and protections.

- Creates traffic filter profiles first.
- Then creates filters/attacks attached to profiles.
- Handles user-friendly parameter mappings.
"""

from ansible.module_utils.basic import AnsibleModule

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

        if not module.check_mode:

            # Step 1: Create profiles
            for profile in tf_profiles:
                profile_name = profile['profile_name']
                api_action = "1" if profile.get('action', 'report_only') == 'report_only' else "0"
                path = f"/mgmt/device/byip/{dp_ip}/config/rsNewTrafficProfileTable/{profile_name}"
                url = f"https://{provider['cc_ip']}{path}"
                payload = {
                    "rsNewTrafficProfileName": profile_name,
                    "rsNewTrafficProfileAction": api_action
                }
                logger.info(f"Creating Traffic Filter profile '{profile_name}'")
                resp = cc._post(url, json=payload)
                created_profiles.append({'profile_name': profile_name, 'response': resp.json()})
                changes_made = True

            # Step 2: Create protections
            for prot in tf_protections:
                profile_name = prot['profile_name']
                protection_name = prot['protection_name']
                path = f"/mgmt/device/byip/{dp_ip}/config/rsNewTrafficFilterTable/{profile_name}/{protection_name}"
                url = f"https://{provider['cc_ip']}{path}"
                payload = map_protection_parameters(prot)
                logger.info(f"Creating Traffic Filter protection '{protection_name}' under profile '{profile_name}'")
                resp = cc._post(url, json=payload)
                created_protections.append({
                    'profile_name': profile_name,
                    'protection_name': protection_name,
                    'response': resp.json()
                })
                changes_made = True

        result['changed'] = changes_made
        result['response'] = {
            'created_profiles': created_profiles,
            'created_protections': created_protections
        }

        debug_info['summary'] = {
            'profiles_created': len(created_profiles),
            'protections_created': len(created_protections),
            'operations_completed': changes_made
        }

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def map_protection_parameters(prot):
    """Map user-friendly values to API values for Traffic Filter protections."""
    TCP_FLAGS_MAP = {'enabled': '2', 'disabled': '1'}
    PACKET_REPORT_MAP = {'enabled': '1', 'disabled': '2'}

    payload = {
        "rsNewTrafficFilterProfileName": prot['profile_name'],
        "rsNewTrafficFilterName": prot['protection_name'],
        "rsNewTrafficFilterMatchCriteria": prot.get('match_criteria', '1'),
        "rsNewTrafficFilterProtocol": '0' if prot.get('protocol', 'any') == 'any' else ('2' if prot.get('protocol')=='tcp' else '3'),
        "rsNewTrafficFilterPacketSize": prot.get('packet_size', ''),
        "rsNewTrafficFilterTCPFlagsSyn": TCP_FLAGS_MAP.get(prot.get('tcp_syn', 'enabled'), '2'),
        "rsNewTrafficFilterTCPFlagsAck": TCP_FLAGS_MAP.get(prot.get('tcp_ack', 'enabled'), '2'),
        "rsNewTrafficFilterTCPFlagsRst": TCP_FLAGS_MAP.get(prot.get('tcp_rst', 'enabled'), '2'),
        "rsNewTrafficFilterTCPFlagsSynAck": TCP_FLAGS_MAP.get(prot.get('tcp_synack', 'enabled'), '2'),
        "rsNewTrafficFilterTCPFlagsFinAck": TCP_FLAGS_MAP.get(prot.get('tcp_finack', 'enabled'), '2'),
        "rsNewTrafficFilterTCPFlagsPshAck": TCP_FLAGS_MAP.get(prot.get('tcp_pshack', 'enabled'), '2'),
        "rsNewTrafficFilterThresholdPPS": str(prot.get('threshold_pps', '10000')),
        "rsNewTrafficFilterThresholdBPS": str(prot.get('threshold_bps', '0')),
        "rsNewTrafficFilterPacketReport": PACKET_REPORT_MAP.get(prot.get('packet_report', 'enabled'), '1'),
        "rsNewTrafficFilterThresholdUsed": str(prot.get('threshold_used', '2')),
        "rsNewTrafficFilterAttackTrackingType": str(prot.get('attack_tracking_type', '0')),
        "rsNewTrafficFilterCustomProtocol": prot.get('custom_protocol', '')
    }
    return payload


def main():
    run_module()

if __name__ == '__main__':
    main()
