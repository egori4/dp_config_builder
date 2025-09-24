# plugins/modules/get_syn_profile.py
"""
Ansible module to fetch DefensePro SYN profiles and associated protections.

- Fetches SYN protections and profiles from DefensePro via CyberController API
- Combines data into a nested structure: profiles -> protections
- Returns a user-friendly structure suitable for playbooks and reporting
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        filter_syn_profile_names=dict(type='list', required=False, default=[])
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    filter_syn_profile_names = module.params['filter_syn_profile_names']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    result = dict(changed=False, profiles=[], debug_info={})

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)
        debug_info = {}

        # Reverse mapping
        PACKET_REPORT_MAP = {'1': 'enable', '2': 'disable'}

        # 1. Get SYN protections
        prot_url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable"
        logger.info(f"Fetching SYN protections from {dp_ip}")
        prot_resp = cc._get(prot_url)
        syn_protections = prot_resp.json().get('rsIDSSYNAttackTable', [])
        debug_info['syn_protections_raw_count'] = len(syn_protections)

        # 2. Get SYN profiles
        prof_url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesTable"
        logger.info(f"Fetching SYN profiles from {dp_ip}")
        prof_resp = cc._get(prof_url)
        syn_profiles = prof_resp.json().get('rsIDSSynProfilesTable', [])
        debug_info['syn_profiles_raw_count'] = len(syn_profiles)

        # 3. Build a protection lookup by name
        prot_by_name = {p.get('rsIDSSYNAttackName'): p for p in syn_protections}

        # 4. Build nested profile structure with snake_case keys
        profiles_dict = {}
        for profile in syn_profiles:
            profile_name = profile.get('rsIDSSynProfilesName', 'DEFAULT_PROFILE')
            protection_name = profile.get('rsIDSSynProfileServiceName')
            if profile_name not in profiles_dict:
                profiles_dict[profile_name] = {'profile_name': profile_name, 'protections': []}

            # Get protection details
            prot_details = prot_by_name.get(protection_name, {})
            prot_struct = {
                'protection_name': protection_name,
                'protection_id': prot_details.get('rsIDSSYNAttackId'),
                'activation_threshold': prot_details.get('rsIDSSYNAttackActivationThreshold'),
                'termination_threshold': prot_details.get('rsIDSSYNAttackTerminationThreshold'),
                'packet_report': PACKET_REPORT_MAP.get(str(prot_details.get('rsIDSSYNAttackPacketReport')), prot_details.get('rsIDSSYNAttackPacketReport')),
                'app_port_group': prot_details.get('rsIDSSYNDestinationAppPortGroup')
            }
            profiles_dict[profile_name]['protections'].append(prot_struct)

        # Apply filter if provided
        all_profiles = list(profiles_dict.values())
        if filter_syn_profile_names:
            filtered_profiles = [p for p in all_profiles if p['profile_name'] in filter_syn_profile_names]
            result['profiles'] = filtered_profiles
            debug_info['filter_applied'] = True
            debug_info['filter_syn_profile_names'] = filter_syn_profile_names
            debug_info['filtered_count'] = len(filtered_profiles)
            debug_info['total_count'] = len(all_profiles)
        else:
            result['profiles'] = all_profiles
            debug_info['filter_applied'] = False
            debug_info['total_count'] = len(all_profiles)

        result['debug_info'] = debug_info
        module.exit_json(**result)

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        # Ensure debug_info exists to prevent fail_json error
        module.fail_json(msg=str(e), debug_info=debug_info or {})

def main():
    run_module()

if __name__ == '__main__':
    main()
