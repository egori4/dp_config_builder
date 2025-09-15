"""
Ansible module to delete DefensePro security policies.

This module handles two types of deletions:
1. Delete only the security policy (simple deletion)
2. Delete security policy and associated profiles (complex deletion with profile cleanup)

The deletion_mode parameter controls the behavior:
- "policy_only": Delete only the policy (default)
- "policy_and_profiles": Delete policy and attempt to clean up associated profiles
"""

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        delete_security_policies=dict(type='list', required=False, default=[])
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Extract provider and setup logging
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    delete_security_policies = module.params['delete_security_policies']
    
    log_level = provider.get('log_level', 'disabled')
    
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    debug_info['input'] = {
        'dp_ip': dp_ip,
        'policies_count': len(delete_security_policies)
    }
    
    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        changes_made = False
        deleted_policies = []
        errors = []
        
        if module.check_mode:
            # Preview mode - show what would be deleted
            planned_operations = []
            for policy_delete in delete_security_policies:
                policy_name = policy_delete.get('policy_name')
                deletion_mode = policy_delete.get('deletion_mode', 'policy_only')
                
                if not policy_name:
                    errors.append("Policy name is required for each deletion operation")
                    continue
                
                operation = {
                    'policy_name': policy_name,
                    'deletion_mode': deletion_mode,
                    'description': f"Delete policy '{policy_name}'"
                }
                
                if deletion_mode == 'policy_and_profiles':
                    operation['description'] += " and associated profiles"
                
                planned_operations.append(operation)
            
            result['response'] = {
                'preview_mode': True,
                'planned_operations': planned_operations,
                'summary': {
                    'total_policies_planned': len(planned_operations),
                    'errors_count': len(errors)
                }
            }
            
            if errors:
                result['response']['errors'] = errors
                
        else:
            # Execution mode - perform actual deletions
            if delete_security_policies:
                logger.info(f"Deleting {len(delete_security_policies)} security policies on {dp_ip}")
                
                for policy_delete in delete_security_policies:
                    policy_name = policy_delete.get('policy_name')
                    deletion_mode = policy_delete.get('deletion_mode', 'policy_only')
                    
                    if not policy_name:
                        error_msg = "Policy name is required for each deletion operation"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue
                    
                    try:
                        if deletion_mode == 'policy_and_profiles':
                            # Use complex deletion endpoint with profile cleanup
                            url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/deletenetworktemplatelist"
                            request_body = {
                                "policiesToDelete": [policy_name]
                            }
                            
                            logger.debug(f"DELETE {url}")
                            logger.debug(f"Request body: {request_body}")
                            
                            resp = cc._delete(url, json=request_body)
                            response_data = resp.json()
                            
                        else:
                            # Simple policy-only deletion
                            url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable/{policy_name}"
                            
                            logger.debug(f"DELETE {url}")
                            logger.debug("Request body: None (simple deletion)")
                            
                            resp = cc._delete(url)
                            response_data = resp.json()
                        
                        if response_data.get('status') == 'ok':
                            deleted_policies.append({
                                'policy_name': policy_name,
                                'deletion_mode': deletion_mode,
                                'status': 'success'
                            })
                            changes_made = True
                            
                            if deletion_mode == 'policy_and_profiles':
                                logger.info(f"Successfully deleted security policy and profiles: {policy_name}")
                            else:
                                logger.info(f"Successfully deleted security policy: {policy_name}")
                        else:
                            error_msg = f"Failed to delete security policy {policy_name}: {response_data}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                            
                    except Exception as e:
                        error_msg = f"Error deleting security policy {policy_name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            
            # Prepare response
            result['response'] = {
                'deleted_policies': deleted_policies,
                'errors': errors,
                'summary': {
                    'total_policies_attempted': len(delete_security_policies),
                    'successful_deletions': len(deleted_policies),
                    'failed_deletions': len(errors)
                }
            }
            
            debug_info['summary'] = {
                'operations_completed': True,
                'policies_deleted': len(deleted_policies),
                'policies_failed': len(errors)
            }
            
        result['changed'] = changes_made
        result['debug_info'] = debug_info
        
        # Determine if we should fail
        if errors and not deleted_policies:
            module.fail_json(msg=f"Security policy deletion failed with {len(errors)} error(s). See response.errors for details.", **result)
        elif errors:
            module.exit_json(msg=f"Security policy deletion completed with {len(errors)} error(s). See response.errors for details.", **result)
        else:
            module.exit_json(**result)
            
    except Exception as e:
        debug_info['error'] = f"Security policy deletion failed: {str(e)}"
        result['debug_info'] = debug_info
        module.fail_json(msg=f"Security policy deletion failed: {str(e)}", **result)

def main():
    run_module()

if __name__ == '__main__':
    main()