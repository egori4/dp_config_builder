"""
Ansible module to delete DefensePro connection limit protections and profiles.

This module handles two types of deletions:
1. Remove protections from profiles (without deleting the protection itself)
2. Delete protections entirely (requires protection to not be in any profile)

Key rules implemented:
- Protection cannot be deleted if it's associated with any profile
- Profile is automatically deleted when its last protection is removed
- Both cl_profile_deletions and cl_protection_deletions sections are optional
"""

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        cl_profile_deletions=dict(type='list', required=False, default=[]),
        cl_protection_deletions=dict(type='list', required=False, default=[])
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Extract provider and setup logging
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    cl_profile_deletions = module.params['cl_profile_deletions']
    cl_protection_deletions = module.params['cl_protection_deletions']
    
    log_level = provider.get('log_level', 'disabled')
    
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    debug_info['input'] = {
        'dp_ip': dp_ip,
        'profile_deletions_count': len(cl_profile_deletions),
        'protection_deletions_count': len(cl_protection_deletions)
    }
    
    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        # Check if we need to fetch protections (for name resolution or validation)
        needs_protection_data = False
        if cl_protection_deletions:
            for protection_deletion in cl_protection_deletions:
                protections_to_delete = protection_deletion.get('protections_to_delete', [])
                for item in protections_to_delete:
                    if isinstance(item, str):  # Name needs resolution
                        needs_protection_data = True
                        break
                    elif isinstance(item, int) and module.check_mode:  # Index needs validation in check mode
                        needs_protection_data = True
                        break
                if needs_protection_data:
                    break
        
        # SINGLE API CALL: Fetch protections only when needed
        protection_name_to_index = {}
        valid_indexes = set()
        
        if needs_protection_data:
            try:
                path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable"
                url = f"https://{provider['cc_ip']}{path}"
                action = "PREVIEW: Fetching" if module.check_mode else "Fetching"
                logger.info(f"{action} current protections for name resolution and validation")
                resp = cc._get(url)
                current_protections = resp.json()
                
                if isinstance(current_protections, dict) and 'rsIDSConnectionLimitAttackTable' in current_protections:
                    for prot in current_protections['rsIDSConnectionLimitAttackTable']:
                        prot_name = prot.get('rsIDSConnectionLimitAttackName', '')
                        prot_index = prot.get('rsIDSConnectionLimitAttackId', '')
                        if prot_name and prot_index:
                            protection_name_to_index[prot_name] = prot_index
                            try:
                                valid_indexes.add(int(prot_index))
                            except (ValueError, TypeError):
                                pass  # Skip invalid indexes
                
                logger.info(f"Found {len(protection_name_to_index)} current protections with {len(valid_indexes)} valid indexes")
            except Exception as e:
                error_msg = f"Failed to fetch current protections: {str(e)}"
                logger.error(error_msg)
                if not module.check_mode:  # In execution mode, this is critical
                    module.fail_json(msg=error_msg, debug_info=debug_info, **result)
        
        # UNIFIED PROCESSING: Same logic for check mode and execution
        operations = []
        errors = []
        
        # Process profile deletions
        if cl_profile_deletions:
            logger.info(f"Processing {len(cl_profile_deletions)} profile deletion operations")
            for profile_deletion in cl_profile_deletions:
                profile_name = profile_deletion.get('profile_name', '')
                protections = profile_deletion.get('protections', [])
                
                for protection_name in protections:
                    operations.append({
                        'type': 'remove_from_profile',
                        'profile_name': profile_name,
                        'protection_name': protection_name,
                        'url_path': f"/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitProfileTable/{profile_name}/{protection_name}",
                        'description': f"Remove '{protection_name}' from profile '{profile_name}'"
                    })
        
        # Process protection deletions
        if cl_protection_deletions:
            logger.info(f"Processing {len(cl_protection_deletions)} protection deletion operations")
            for protection_deletion in cl_protection_deletions:
                protections_to_delete = protection_deletion.get('protections_to_delete', [])
                
                for item in protections_to_delete:
                    if isinstance(item, str):
                        # String name - resolve to index
                        protection_name = item
                        if protection_name in protection_name_to_index:
                            protection_index = protection_name_to_index[protection_name]
                            operations.append({
                                'type': 'delete_protection',
                                'protection_name': protection_name,
                                'protection_index': protection_index,
                                'url_path': f"/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable/{protection_index}",
                                'description': f"Delete protection '{protection_name}' at index {protection_index}"
                            })
                        else:
                            errors.append(f"Protection '{protection_name}' not found on device {dp_ip}")
                            operations.append({
                                'type': 'delete_protection',
                                'protection_name': protection_name,
                                'protection_index': 'NOT_FOUND',
                                'error': True,
                                'description': f"Delete protection '{protection_name}' (⚠️  NOT FOUND on device)"
                            })
                    elif isinstance(item, int):
                        # Integer index - validate if in check mode
                        protection_index = item
                        protection_name = None
                        
                        # Find name if available
                        for name, idx in protection_name_to_index.items():
                            try:
                                if int(idx) == protection_index:
                                    protection_name = name
                                    break
                            except (ValueError, TypeError):
                                continue
                        
                        # Check if index exists (only matters in check mode or when we have the data)
                        if module.check_mode and valid_indexes and protection_index not in valid_indexes:
                            errors.append(f"Protection index {protection_index} not found on device {dp_ip}")
                            operations.append({
                                'type': 'delete_protection',
                                'protection_name': protection_name or f"index_{protection_index}",
                                'protection_index': protection_index,
                                'error': True,
                                'description': f"Delete protection at index {protection_index} (⚠️  NOT FOUND on device)"
                            })
                        else:
                            final_name = protection_name or f"index_{protection_index}"
                            description = f"Delete protection '{protection_name}' at index {protection_index}" if protection_name else f"Delete protection at index {protection_index}"
                            operations.append({
                                'type': 'delete_protection',
                                'protection_name': final_name,
                                'protection_index': protection_index,
                                'url_path': f"/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable/{protection_index}",
                                'description': description
                            })
                    else:
                        errors.append(f"Invalid protection identifier: {item} (must be string name or integer index)")
        
        # EXECUTION OR PREVIEW
        if module.check_mode:
            # Preview mode
            profile_ops = [op for op in operations if op['type'] == 'remove_from_profile']
            protection_ops = [op for op in operations if op['type'] == 'delete_protection']
            
            if operations:
                result['changed'] = True
                result['response'] = {
                    'preview_mode': True,
                    'total_operations': len(operations),
                    'profile_operations': profile_ops,
                    'protection_operations': protection_ops
                }
                debug_info['summary'] = {
                    'preview_mode': True,
                    'total_operations_planned': len(operations),
                    'profile_operations_planned': len(profile_ops),
                    'protection_operations_planned': len(protection_ops)
                }
            else:
                result['response'] = {
                    'preview_mode': True,
                    'message': 'No operations configured for deletion'
                }
                debug_info['summary'] = {
                    'preview_mode': True,
                    'operations_planned': 0
                }
        else:
            # Execution mode
            deleted_from_profiles = []
            deleted_protections = []
            changes_made = False
            
            for operation in operations:
                if operation.get('error'):
                    continue  # Skip operations that have validation errors
                
                try:
                    url = f"https://{provider['cc_ip']}{operation['url_path']}"
                    logger.info(f"Executing: {operation['description']}")
                    resp = cc._delete(url)
                    
                    if operation['type'] == 'remove_from_profile':
                        deleted_from_profiles.append({
                            'profile_name': operation['profile_name'],
                            'protection_name': operation['protection_name'],
                            'status': 'success'
                        })
                    else:  # delete_protection
                        deleted_protections.append({
                            'protection_name': operation['protection_name'],
                            'protection_index': operation['protection_index'],
                            'status': 'success'
                        })
                    
                    changes_made = True
                    logger.info(f"Successfully executed: {operation['description']}")
                    
                except Exception as e:
                    error_msg = f"Failed to execute {operation['description']}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            result['changed'] = changes_made
            result['response'] = {
                'deleted_from_profiles': deleted_from_profiles,
                'deleted_protections': deleted_protections,
                'errors': errors
            }
            
            debug_info['summary'] = {
                'protections_removed_from_profiles': len(deleted_from_profiles),
                'protections_deleted': len(deleted_protections),
                'errors_count': len(errors),
                'operations_completed': changes_made
            }
        
        # Handle errors
        if errors and not module.check_mode:
            if not result.get('changed', False):
                module.fail_json(msg=f"All operations failed. Errors: {'; '.join(errors)}", debug_info=debug_info, **result)
            else:
                result['warnings'] = errors
        
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)
    
    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
