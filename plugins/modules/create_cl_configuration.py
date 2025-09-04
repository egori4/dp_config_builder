# plugins/modules/manage_cl_configuration.py
"""
Unified Ansible module to manage DefensePro connection limit protections and profiles.

This module handles both connection limit protection creation and profile creation
in a single operation, simplifying the playbook structure and improving error handling.
"""

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        cl_protections=dict(type='list', required=False, default=[]),
        cl_profiles=dict(type='list', required=False, default=[])
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Extract provider and setup logging
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    cl_protections = module.params['cl_protections']
    cl_profiles = module.params['cl_profiles']
    
    log_level = provider.get('log_level', 'disabled')
    
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    debug_info['input'] = {
        'dp_ip': dp_ip,
        'protections_count': len(cl_protections),
        'profiles_count': len(cl_profiles)
    }
    
    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        changes_made = False
        created_protections = []
        created_profiles = []
        
        if not module.check_mode:
            # Step 1: Create protections if any are defined
            if cl_protections:
                logger.info(f"Creating {len(cl_protections)} connection limit protections on {dp_ip}")
                
                for i, protection in enumerate(cl_protections):
                    protection_name = protection['name']
                    
                    # Map user-friendly values to API values
                    api_params = map_protection_parameters(protection)
                    
                    # Determine index - use specified or default to 0
                    index = protection.get('index', 0)
                    
                    # Refresh state for subsequent protections to avoid API caching
                    if i > 0:
                        refresh_device_state(cc, dp_ip, provider, logger)
                    
                    # Create protection
                    path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable/{index}"
                    url = f"https://{provider['cc_ip']}{path}"
                    
                    logger.info(f"Creating protection '{protection_name}' at index {index}")
                    resp = cc._post(url, json=api_params)
                    data = resp.json()
                    
                    created_protections.append({
                        'name': protection_name,
                        'index': index,
                        'response': data
                    })
                    changes_made = True
            
            # Step 2: Create profiles if any are defined
            if cl_profiles:
                logger.info(f"Creating {len(cl_profiles)} connection limit profiles on {dp_ip}")
                
                for profile in cl_profiles:
                    profile_name = profile['name']
                    protections = profile.get('protections', [])
                    
                    for protection_name in protections:
                        # Create profile with attached protection
                        path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitProfileTable/{profile_name}/{protection_name}"
                        url = f"https://{provider['cc_ip']}{path}"
                        
                        body = {
                            "rsIDSConnectionLimitProfileName": profile_name,
                            "rsIDSConnectionLimitProfileAttackName": protection_name
                        }
                        
                        logger.info(f"Creating profile '{profile_name}' with protection '{protection_name}'")
                        resp = cc._post(url, json=body)
                        data = resp.json()
                        
                        created_profiles.append({
                            'profile_name': profile_name,
                            'protection_name': protection_name,
                            'response': data
                        })
                        changes_made = True
        
        # Prepare result
        result['changed'] = changes_made
        result['response'] = {
            'created_protections': created_protections,
            'created_profiles': created_profiles
        }
        
        debug_info['summary'] = {
            'protections_created': len(created_protections),
            'profiles_created': len(created_profiles),
            'operations_completed': changes_made
        }
        
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)
    
    result['debug_info'] = debug_info
    module.exit_json(**result)

def map_protection_parameters(protection):
    """Map user-friendly parameter values to API values."""
    
    # User-friendly mappings based on working create_cl_protection.py
    PROTOCOL_MAP = {'tcp': '2', 'udp': '3'}  # Fixed: was using '6', '17'
    TRACKING_TYPE_MAP = {'src_ip': '2', 'dst_ip': '3', 'src_and_dest_ip': '4', 'dst_ip_and_port': '5'}
    ACTION_MAP = {'report_only': '0', 'drop': '10'}  # Fixed: was reversed
    PACKET_REPORT_MAP = {'enable': '1', 'disable': '2'}
    PROTECTION_TYPE_MAP = {'cps': '1', 'concurrent_connections': '2'}
    
    # Map parameters with defaults
    api_params = {
        "rsIDSConnectionLimitAttackName": protection['name'],
        "rsIDSConnectionLimitAttackProtocol": PROTOCOL_MAP.get(protection.get('protocol', 'tcp'), '2'),
        "rsIDSConnectionLimitAttackAppPort": protection.get('app_port_group', ''),
        "rsIDSConnectionLimitAttackThreshold": str(protection.get('threshold', '50')),
        "rsIDSConnectionLimitAttackTrackingType": TRACKING_TYPE_MAP.get(protection.get('tracking_type', 'dst_ip'), '3'),
        "rsIDSConnectionLimitAttackReportMode": ACTION_MAP.get(protection.get('action', 'drop'), '10'),
        "rsIDSConnectionLimitAttackPacketReport": PACKET_REPORT_MAP.get(protection.get('packet_report', 'disable'), '2'),
        "rsIDSConnectionLimitAttackType": PROTECTION_TYPE_MAP.get(protection.get('protection_type', 'cps'), '1')
    }
    
    return api_params

def refresh_device_state(cc, dp_ip, provider, logger):
    """Refresh device state to avoid API caching issues."""
    try:
        path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable"
        url = f"https://{provider['cc_ip']}{path}"
        cc._get(url)
        logger.debug(f"Refreshed device state for {dp_ip}")
    except Exception as e:
        logger.debug(f"State refresh failed (non-critical): {str(e)}")

def main():
    run_module()

if __name__ == '__main__':
    main()
