# plugins/modules/delete_network_class.py
"""
Unified Ansible module to delete DefensePro network classes via Radware CyberController API.

This module handles deletion of multiple network class groups in a single operation,
following the unified pattern from delete_cl_configuration.
"""

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        delete_networks=dict(type='list', required=False, default=[])
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Extract provider and setup logging
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    delete_networks = module.params['delete_networks']
    
    log_level = provider.get('log_level', 'disabled')
    
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    debug_info['input'] = {
        'dp_ip': dp_ip,
        'delete_networks_count': len(delete_networks)
    }
    
    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        changes_made = False
        deleted_groups = []
        errors = []
        
        if not module.check_mode:
            # Process each network group deletion
            if delete_networks:
                logger.info(f"Deleting {len(delete_networks)} network groups on {dp_ip}")
                
                for network_deletion in delete_networks:
                    class_name = network_deletion.get('class_name', '')
                    index = network_deletion.get('index', '')
                    
                    if not class_name:
                        error_msg = "Network deletion missing required 'class_name' field"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue
                    
                    if index == '' or index is None:
                        error_msg = f"Network deletion for class '{class_name}' missing required 'index' field"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue
                    
                    try:
                        # Delete network group
                        path = f"/mgmt/device/byip/{dp_ip}/config/rsBWMNetworkTable/{class_name}/{index}"
                        url = f"https://{provider['cc_ip']}{path}"
                        
                        logger.info(f"Deleting network group '{class_name}[{index}]'")
                        logger.debug(f"Request URL: {url}")
                        
                        resp = cc._delete(url)
                        data = resp.json()
                        
                        deleted_groups.append({
                            'class_name': class_name,
                            'index': index,
                            'status': 'success',
                            'response': data
                        })
                        changes_made = True
                        logger.info(f"Successfully deleted network group '{class_name}[{index}]'")
                        
                    except Exception as e:
                        error_msg = f"Failed to delete network group '{class_name}[{index}]': {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        
                        # Add to deleted_groups with error status for reporting
                        deleted_groups.append({
                            'class_name': class_name,
                            'index': index,
                            'status': 'failed',
                            'error': str(e)
                        })
            
            result['changed'] = changes_made
            result['response'] = {
                'deleted_groups': deleted_groups,
                'errors': errors,
                'summary': {
                    'total_groups_attempted': len(deleted_groups),
                    'successful_deletions': len([g for g in deleted_groups if g['status'] == 'success']),
                    'failed_deletions': len([g for g in deleted_groups if g['status'] == 'failed'])
                }
            }
            
            debug_info['summary'] = {
                'groups_deleted': len([g for g in deleted_groups if g['status'] == 'success']),
                'groups_failed': len([g for g in deleted_groups if g['status'] == 'failed']),
                'errors_count': len(errors),
                'operations_completed': changes_made
            }
            
        else:
            # Check mode - show what would be deleted
            planned_operations = []
            
            if delete_networks:
                for network_deletion in delete_networks:
                    class_name = network_deletion.get('class_name', '')
                    index = network_deletion.get('index', '')
                    
                    if not class_name:
                        errors.append("Network deletion missing required 'class_name' field")
                        continue
                    
                    if index == '' or index is None:
                        errors.append(f"Network deletion for class '{class_name}' missing required 'index' field")
                        continue
                    
                    planned_operations.append({
                        'class_name': class_name,
                        'index': index,
                        'description': f"Delete network group '{class_name}[{index}]'"
                    })
            
            if planned_operations:
                result['changed'] = True
                result['response'] = {
                    'preview_mode': True,
                    'planned_operations': planned_operations,
                    'total_operations': len(planned_operations)
                }
                debug_info['summary'] = {
                    'preview_mode': True,
                    'operations_planned': len(planned_operations)
                }
            else:
                result['response'] = {
                    'preview_mode': True,
                    'message': 'No network groups configured for deletion'
                }
                debug_info['summary'] = {
                    'preview_mode': True,
                    'operations_planned': 0
                }
        
        # Handle errors
        if errors:
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
