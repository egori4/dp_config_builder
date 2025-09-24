# plugins/modules/update_policies.py
"""
Ansible module to apply DefensePro configuration updates (policy updates) via Radware CyberController API.

This module applies pending configuration changes to DefensePro devices by calling the update policies API.
Device must be locked before calling this operation.
Follows the unified architecture pattern established in other modules.
"""

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True)
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Extract provider and setup logging
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    
    log_level = provider.get('log_level', 'disabled')
    
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    debug_info['input'] = {
        'dp_ip': dp_ip
    }
    
    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        if module.check_mode:
            # Preview mode - show what would be updated
            logger.info(f"PREVIEW: Would apply policy updates to DefensePro {dp_ip}")
            
            planned_operations = [{
                'operation': 'apply_policy_updates',
                'device': dp_ip,
                'description': f"Apply pending configuration changes to {dp_ip}"
            }]
            
            result.update({
                'changed': True,  # Policy updates always considered a change
                'response': {
                    'preview_mode': True,
                    'planned_operations': planned_operations,
                    'message': f"PREVIEW MODE - Would apply policy updates to {dp_ip}"
                },
                'debug_info': debug_info
            })
            
        else:
            # Actual execution mode
            logger.info(f"Applying policy updates to DefensePro {dp_ip}")
            
            try:
                # Construct the correct API URL with full schema and host
                url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/updatepolicies"
                
                logger.info(f"Applying policy updates to {dp_ip}")
                logger.debug(f"Policy update URL: {url}")
                
                # No payload needed for this API call
                resp = cc._post(url)
                
                if resp.status_code == 200:
                    logger.info(f"Successfully applied policy updates to {dp_ip}")
                    
                    # Try to parse response for additional info
                    try:
                        response_data = resp.json() if hasattr(resp, 'json') else {}
                    except Exception:
                        response_data = {"response_text": str(resp.text) if hasattr(resp, 'text') else "Success"}
                    
                    # Determine success status
                    response_str = str(response_data).lower()
                    warnings = []
                    
                    # Check for known error patterns in response
                    error_patterns = ['error', 'failed', 'exception', 'timeout', 'denied']
                    if any(pattern in response_str for pattern in error_patterns):
                        status = "failed"
                        message = "API response indicates failure"
                        logger.error(f"Policy update failed for {dp_ip}: {response_data}")
                        # Fail the module on detected failure
                        module.fail_json(
                            msg=f"Policy update failed for {dp_ip}: {message}",
                            response=response_data,
                            debug_info=debug_info
                        )
                    else:
                        status = "success"
                        message = f"Policy updates applied successfully on {dp_ip}"
                        
                        # Add warning about API response reliability
                        if not any(pattern in response_str for pattern in ['success', 'completed', 'applied', 'updated']):
                            warnings.append("API response does not provide clear success confirmation - verify policy status manually")
                    
                    result.update({
                        'changed': True,
                        'response': {
                            'status': status,
                            'message': message,
                            'api_response': response_data,
                            'warnings': warnings if warnings else None
                        },
                        'debug_info': debug_info
                    })
                    
                else:
                    error_msg = f"Policy update failed for {dp_ip}: HTTP {resp.status_code} - {resp.text}"
                    logger.error(error_msg)
                    module.fail_json(
                        msg=error_msg,
                        status_code=resp.status_code,
                        response_text=resp.text,
                        debug_info=debug_info
                    )
                    
            except Exception as e:
                error_msg = f"Error applying policy updates to {dp_ip}: {str(e)}"
                logger.error(error_msg)
                module.fail_json(
                    msg=error_msg,
                    exception=str(e),
                    debug_info=debug_info
                )
    
    except Exception as e:
        error_msg = f"Module initialization failed: {str(e)}"
        debug_info['error'] = error_msg
        module.fail_json(msg=error_msg, debug_info=debug_info)
    
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()