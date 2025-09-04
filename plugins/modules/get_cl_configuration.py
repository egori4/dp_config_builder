"""
Ansible module to fetch DefensePro connection limit profiles, associated protections, and protection settings.

- Fetches all profiles and protections from DefensePro via CyberController API
- Combines and maps data to a nested structure: profiles -> protections -> subsettings
- All mapping/translation logic is handled in Python (reverse of create/edit logic)
- Returns a user-friendly nested response for use in playbooks or reporting
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True)
    )
    result = dict(changed=False, profiles=[], debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'], log_level=log_level, logger=logger)
    debug_info = {}

    # Reverse mappings (API value -> user-friendly)
    PROTOCOL_MAP = {'2': 'tcp', '3': 'udp'}
    TRACKING_TYPE_MAP = {'2': 'src_ip', '3': 'dst_ip', '4': 'src_and_dest_ip', '5': 'dst_ip_and_port'}
    ACTION_MAP = {'0': 'report_only', '10': 'drop'}
    PACKET_REPORT_MAP = {'1': 'enable', '2': 'disable'}
    PROTECTION_TYPE_MAP = {'1': 'cps', '2': 'concurrent_connections'}

    try:
        # 1. Get all profiles
        profile_path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitProfileTable"
        profile_url = f"https://{provider['cc_ip']}{profile_path}"
        logger.info(f"Fetching connection limit profiles from {dp_ip}")
        resp = cc._get(profile_url)
        profiles_raw = resp.json().get('rsIDSConnectionLimitProfileTable', [])
        debug_info['profiles_raw_count'] = len(profiles_raw)

        # 2. Get all protections
        prot_path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable"
        prot_url = f"https://{provider['cc_ip']}{prot_path}"
        logger.info(f"Fetching connection limit protections from {dp_ip}")
        resp = cc._get(prot_url)
        protections_raw = resp.json().get('rsIDSConnectionLimitAttackTable', [])
        debug_info['protections_raw_count'] = len(protections_raw)

        # 3. Build protection lookup by ID
        prot_by_id = {p['rsIDSConnectionLimitAttackId']: p for p in protections_raw}

        # 4. Build nested profile structure
        profiles = {}
        for entry in profiles_raw:
            prof_name = entry['rsIDSConnectionLimitProfileName']
            prot_id = entry['rsIDSConnectionLimitProfileAttackId']
            prot_name = entry['rsIDSConnectionLimitProfileAttackName']
            if prof_name not in profiles:
                profiles[prof_name] = {'profile_name': prof_name, 'protections': []}
            # Find protection details
            prot = prot_by_id.get(prot_id, {})
            # Map/translate protection fields (back to dict for easier use)
            prot_raw = prot_by_id.get(prot_id, {})
            prot_settings = {
                'protection_name': prot_raw.get('rsIDSConnectionLimitAttackName', prot_name),
                'protection_id': prot_raw.get('rsIDSConnectionLimitAttackId', prot_id),
                'protection_type': PROTECTION_TYPE_MAP.get(prot_raw.get('rsIDSConnectionLimitAttackType', ''), prot_raw.get('rsIDSConnectionLimitAttackType', '')),
                'tracking_type': TRACKING_TYPE_MAP.get(prot_raw.get('rsIDSConnectionLimitAttackTrackingType', ''), prot_raw.get('rsIDSConnectionLimitAttackTrackingType', '')),
                'protocol': PROTOCOL_MAP.get(prot_raw.get('rsIDSConnectionLimitAttackProtocol', ''), prot_raw.get('rsIDSConnectionLimitAttackProtocol', '')),
                'threshold': prot_raw.get('rsIDSConnectionLimitAttackThreshold', ''),
                'action': ACTION_MAP.get(prot_raw.get('rsIDSConnectionLimitAttackReportMode', ''), prot_raw.get('rsIDSConnectionLimitAttackReportMode', '')),
                'packet_report': PACKET_REPORT_MAP.get(prot_raw.get('rsIDSConnectionLimitAttackPacketReport', ''), prot_raw.get('rsIDSConnectionLimitAttackPacketReport', '')),
                'app_port_group': prot_raw.get('rsIDSConnectionLimitAttackAppPort', '')
            }
            profiles[prof_name]['protections'].append(prot_settings)

        result['profiles'] = list(profiles.values())
        result['debug_info'] = debug_info
        module.exit_json(**result)
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

def main():
    run_module()

if __name__ == '__main__':
    main()
