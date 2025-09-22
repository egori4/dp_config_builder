# plugins/modules/edit_network_class.py
"""
Unified Ansible module to edit DefensePro network classes via Radware CyberController API.

This module handles editing of multiple network class groups in a single operation,
following the unified pattern from other enhanced modules.
"""

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        edit_networks=dict(type='list', required=False, default=[])
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Extract provider and setup logging
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    edit_networks = module.params['edit_networks']
    
    log_level = provider.get('log_level', 'disabled')
    
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    debug_info['input'] = {
        'dp_ip': dp_ip,
        'edit_networks_count': len(edit_networks)
    }
    
    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        changes_made = False
        edited_groups = []
        errors = []
        
        if not module.check_mode:
            # Process each network group edit
            if edit_networks:
                logger.info(f"Editing {len(edit_networks)} network groups on {dp_ip}")
                
                for network_edit in edit_networks:
                    class_name = network_edit.get('class_name', '')
                    index = network_edit.get('index', '')
                    address = network_edit.get('address', '')
                    mask = network_edit.get('mask', '')
                    
                    if not class_name:
                        error_msg = "Network edit missing required 'class_name' field"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue
                    
                    if index == '' or index is None:
                        error_msg = f"Network edit for class '{class_name}' missing required 'index' field"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue
                    
                    if not address:
                        error_msg = f"Network edit for class '{class_name}[{index}]' missing required 'address' field"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue
                    
                    if not mask:
                        error_msg = f"Network edit for class '{class_name}[{index}]' missing required 'mask' field"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue
                    
                    try:
                        # Edit network group
                        path = f"/mgmt/device/byip/{dp_ip}/config/rsBWMNetworkTable/{class_name}/{index}"
                        url = f"https://{provider['cc_ip']}{path}"
                        
                        body = {
                            "rsBWMNetworkName": class_name,
                            "rsBWMNetworkAddress": address,
                            "rsBWMNetworkMask": mask
                        }
                        
                        logger.info(f"Editing network group '{class_name}[{index}]' to {address}/{mask}")
                        logger.debug(f"Request URL: {url}")
                        logger.debug(f"Request body: {body}")
                        
                        resp = cc._put(url, json=body)
                        data = resp.json()
                        
                        edited_groups.append({
                            'class_name': class_name,
                            'index': index,
                            'address': address,
                            'mask': mask,
                            'status': 'success',
                            'response': data
                        })
                        changes_made = True
                        logger.info(f"Successfully edited network group '{class_name}[{index}]'")
                        
                    except Exception as e:
                        error_msg = f"Failed to edit network group '{class_name}[{index}]' ({address}/{mask}): {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        
                        # Add to edited_groups with error status for reporting
                        edited_groups.append({
                            'class_name': class_name,
                            'index': index,
                            'address': address,
                            'mask': mask,
                            'status': 'failed',
                            'error': str(e)
                        })
            
            result['changed'] = changes_made
            result['response'] = {
                'edited_groups': edited_groups,
                'errors': errors,
                'summary': {
                    'total_groups_attempted': len(edited_groups),
                    'successful_edits': len([g for g in edited_groups if g['status'] == 'success']),
                    'failed_edits': len([g for g in edited_groups if g['status'] == 'failed'])
                }
            }
            
            debug_info['summary'] = {
                'groups_edited': len([g for g in edited_groups if g['status'] == 'success']),
                'groups_failed': len([g for g in edited_groups if g['status'] == 'failed']),
                'errors_count': len(errors),
                'operations_completed': changes_made
            }
            
        else:
            # Check mode - show what would be edited
            planned_operations = []
            
            if edit_networks:
                for network_edit in edit_networks:
                    class_name = network_edit.get('class_name', '')
                    index = network_edit.get('index', '')
                    address = network_edit.get('address', '')
                    mask = network_edit.get('mask', '')
                    
                    if not class_name:
                        errors.append("Network edit missing required 'class_name' field")
                        continue
                    
                    if index == '' or index is None:
                        errors.append(f"Network edit for class '{class_name}' missing required 'index' field")
                        continue
                    
                    if not address:
                        errors.append(f"Network edit for class '{class_name}[{index}]' missing required 'address' field")
                        continue
                    
                    if not mask:
                        errors.append(f"Network edit for class '{class_name}[{index}]' missing required 'mask' field")
                        continue
                    
                    planned_operations.append({
                        'class_name': class_name,
                        'index': index,
                        'address': address,
                        'mask': mask,
                        'description': f"Edit network group '{class_name}[{index}]' to {address}/{mask}"
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
                    'message': 'No network groups configured for editing'
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
