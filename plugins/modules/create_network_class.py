# plugins/modules/create_network_class.py
"""
Unified Ansible module to create DefensePro network classes via Radware CyberController API.

This module handles creation of multiple network classes with their network groups in a single operation.
"""

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        netclasses=dict(type='list', required=False, default=[])
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Extract provider and setup logging
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    netclasses = module.params['netclasses']
    
    log_level = provider.get('log_level', 'disabled')
    
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    debug_info['input'] = {
        'dp_ip': dp_ip,
        'netclasses_count': len(netclasses),
        'total_groups': sum(len(nc.get('groups', [])) for nc in netclasses)
    }
    
    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        changes_made = False
        created_groups = []
        errors = []
        
        if not module.check_mode:
            # Process each network class
            if netclasses:
                logger.info(f"Creating {len(netclasses)} network classes with {debug_info['input']['total_groups']} total groups on {dp_ip}")
                
                for netclass in netclasses:
                    class_name = netclass.get('name', '')
                    groups = netclass.get('groups', [])
                    
                    if not class_name:
                        error_msg = "Network class missing required 'name' field"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue
                    
                    logger.info(f"Processing network class '{class_name}' with {len(groups)} groups")
                    
                    # Process each group within the class
                    for index, group in enumerate(groups):
                        address = group.get('address', '')
                        mask = group.get('mask', '')
                        
                        if not address or not mask:
                            error_msg = f"Group at index {index} in class '{class_name}' missing address or mask"
                            errors.append(error_msg)
                            logger.error(error_msg)
                            continue
                        
                        try:
                            # Create network group
                            path = f"/mgmt/device/byip/{dp_ip}/config/rsBWMNetworkTable/{class_name}/{index}"
                            url = f"https://{provider['cc_ip']}{path}"
                            
                            body = {
                                "rsBWMNetworkName": class_name,
                                "rsBWMNetworkSubIndex": index,
                                "rsBWMNetworkAddress": address,
                                "rsBWMNetworkMask": mask,
                                "rsBWMNetworkMode": "1"
                            }
                            
                            logger.info(f"Creating network group '{class_name}[{index}]': {address}/{mask}")
                            logger.debug(f"Request URL: {url}")
                            logger.debug(f"Request body: {body}")
                            
                            resp = cc._post(url, json=body)
                            data = resp.json()
                            
                            created_groups.append({
                                'class_name': class_name,
                                'index': index,
                                'address': address,
                                'mask': mask,
                                'status': 'success',
                                'response': data
                            })
                            changes_made = True
                            logger.info(f"Successfully created network group '{class_name}[{index}]'")
                            
                        except Exception as e:
                            error_msg = f"Failed to create network group '{class_name}[{index}]' ({address}/{mask}): {str(e)}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                            
                            # Add to created_groups with error status for reporting
                            created_groups.append({
                                'class_name': class_name,
                                'index': index,
                                'address': address,
                                'mask': mask,
                                'status': 'failed',
                                'error': str(e)
                            })
            
            result['changed'] = changes_made
            result['response'] = {
                'created_groups': created_groups,
                'errors': errors,
                'summary': {
                    'total_groups_attempted': len(created_groups),
                    'successful_groups': len([g for g in created_groups if g['status'] == 'success']),
                    'failed_groups': len([g for g in created_groups if g['status'] == 'failed'])
                }
            }
            
            debug_info['summary'] = {
                'groups_created': len([g for g in created_groups if g['status'] == 'success']),
                'groups_failed': len([g for g in created_groups if g['status'] == 'failed']),
                'errors_count': len(errors),
                'operations_completed': changes_made
            }
            
        else:
            # Check mode - show what would be created
            planned_operations = []
            
            if netclasses:
                for netclass in netclasses:
                    class_name = netclass.get('name', '')
                    groups = netclass.get('groups', [])
                    
                    if not class_name:
                        errors.append("Network class missing required 'name' field")
                        continue
                    
                    for index, group in enumerate(groups):
                        address = group.get('address', '')
                        mask = group.get('mask', '')
                        
                        if not address or not mask:
                            errors.append(f"Group at index {index} in class '{class_name}' missing address or mask")
                            continue
                        
                        planned_operations.append({
                            'class_name': class_name,
                            'index': index,
                            'address': address,
                            'mask': mask,
                            'description': f"Create network group '{class_name}[{index}]': {address}/{mask}"
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
                    'message': 'No network classes configured for creation'
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
