# plugins/modules/edit_security_policy.py
"""
Unified Ansible module to edit DefensePro security policies via Radware CyberController API.

This module handles editing of multiple security policies in a single operation,
following the unified pattern from other enhanced modules. Only specified parameters
are modified, leaving other settings unchanged.
"""

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        edit_security_policies=dict(type='list', required=False, default=[])
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Extract provider and setup logging
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    edit_security_policies = module.params['edit_security_policies']
    
    log_level = provider.get('log_level', 'disabled')
    
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    debug_info['input'] = {
        'dp_ip': dp_ip,
        'policies_count': len(edit_security_policies)
    }
    
    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        changes_made = False
        edited_policies = []
        errors = []
        
        if module.check_mode:
            # Preview mode - show what would be edited
            planned_operations = []
            for policy_edit in edit_security_policies:
                policy_name = policy_edit.get('policy_name')
                if not policy_name:
                    errors.append("Policy name is required for each edit operation")
                    continue
                
                # Determine what changes would be made
                changes = []
                for key, value in policy_edit.items():
                    if key != 'policy_name' and value is not None:
                        changes.append(f"{key}: {value}")
                
                planned_operations.append({
                    'policy_name': policy_name,
                    'changes': changes
                })
            
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
            # Execution mode - perform actual edits
            if edit_security_policies:
                logger.info(f"Editing {len(edit_security_policies)} security policies on {dp_ip}")
                
                for policy_edit in edit_security_policies:
                    policy_name = policy_edit.get('policy_name')
                    if not policy_name:
                        error_msg = "Policy name is required for each edit operation"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue
                    
                    try:
                        # Map user-friendly values to API values for provided parameters only
                        api_params = map_security_policy_parameters(policy_edit)
                        
                        # Construct API request body with only specified parameters
                        request_body = {}
                        changes_applied = []
                        
                        # Add optional parameters only if specified by user
                        if 'src_network' in policy_edit and policy_edit['src_network'] is not None:
                            request_body["rsIDSNewRulesSource"] = policy_edit['src_network']
                            changes_applied.append(f"src_network: {policy_edit['src_network']}")
                        
                        if 'dst_network' in policy_edit and policy_edit['dst_network'] is not None:
                            request_body["rsIDSNewRulesDestination"] = policy_edit['dst_network']
                            changes_applied.append(f"dst_network: {policy_edit['dst_network']}")
                        
                        # Use mapped values for the following parameters if they were provided
                        if 'direction' in api_params:
                            request_body["rsIDSNewRulesDirection"] = api_params['direction']
                            changes_applied.append(f"direction: {policy_edit['direction']}")
                        
                        if 'state' in api_params:
                            request_body["rsIDSNewRulesState"] = api_params['state']
                            changes_applied.append(f"state: {policy_edit['state']}")
                        
                        if 'action' in api_params:
                            request_body["rsIDSNewRulesAction"] = api_params['action']
                            changes_applied.append(f"action: {policy_edit['action']}")
                        
                        if 'packet_reporting_status' in api_params:
                            request_body["rsIDSNewRulesPacketReportingStatus"] = api_params['packet_reporting_status']
                            changes_applied.append(f"packet_reporting_status: {policy_edit['packet_reporting_status']}")
                        
                        if 'priority' in policy_edit and policy_edit['priority'] is not None:
                            request_body["rsIDSNewRulesPriority"] = str(policy_edit['priority'])
                            changes_applied.append(f"priority: {policy_edit['priority']}")
                        
                        # Add profile bindings
                        profile_mappings = {
                            "rsIDSNewRulesProfileAppsec": ('signature_protection_profile', policy_edit.get('signature_protection_profile')),
                            "rsIDSNewRulesProfileConlmt": ('connection_limit_profile', policy_edit.get('connection_limit_profile')),
                            "rsIDSNewRulesProfileNetflood": ('bdos_profile', policy_edit.get('bdos_profile')),
                            "rsIDSNewRulesProfileSyn": ('syn_protection_profile', policy_edit.get('syn_protection_profile')),
                            "rsIDSNewRulesProfileDns": ('dns_flood_profile', policy_edit.get('dns_flood_profile')),
                            "rsIDSNewRulesProfileHttps": ('https_flood_profile', policy_edit.get('https_flood_profile')),
                            "rsIDSNewRulesProfileTraffic": ('traffic_filters_profile', policy_edit.get('traffic_filters_profile')),
                            "rsIDSNewRulesProfileErt": ('ert_attackers_feed_profile', policy_edit.get('ert_attackers_feed_profile')),
                            "rsIDSNewRulesProfileGeo": ('geo_feed_profile', policy_edit.get('geo_feed_profile')),
                            "rsIDSNewRulesProfileOut": ('out_of_state_profile', policy_edit.get('out_of_state_profile'))
                        }
                        
                        for api_key, (user_key, profile_value) in profile_mappings.items():
                            # Only include profiles that were explicitly specified by the user
                            if user_key in policy_edit:
                                # Handle both empty strings (detachment) and non-empty strings (attachment)
                                if profile_value is None:
                                    profile_value = ""
                                request_body[api_key] = str(profile_value).strip()
                                action_word = "detached" if not profile_value else "attached"
                                changes_applied.append(f"{user_key}: {action_word} ({profile_value})")
                        
                        # Only send request if there are changes to make
                        if not request_body:
                            logger.warning(f"No changes specified for policy {policy_name}, skipping")
                            continue
                        
                        # Make the API call
                        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable/{policy_name}"
                        logger.debug(f"PUT {url}")
                        logger.debug(f"Request body: {request_body}")
                        
                        resp = cc._put(url, json=request_body)
                        response_data = resp.json()
                        
                        if response_data.get('status') == 'ok':
                            edited_policies.append({
                                'policy_name': policy_name,
                                'status': 'success',
                                'changes_applied': changes_applied
                            })
                            changes_made = True
                            logger.info(f"Successfully edited security policy: {policy_name}")
                        else:
                            error_msg = f"Failed to edit security policy {policy_name}: {response_data}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                            
                    except Exception as e:
                        error_msg = f"Error editing security policy {policy_name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            
            # Prepare response
            result['response'] = {
                'edited_policies': edited_policies,
                'errors': errors,
                'summary': {
                    'total_policies_attempted': len(edit_security_policies),
                    'successful_edits': len(edited_policies),
                    'failed_edits': len(errors)
                }
            }
            
            debug_info['summary'] = {
                'operations_completed': True,
                'policies_edited': len(edited_policies),
                'policies_failed': len(errors)
            }
            
        result['changed'] = changes_made
        result['debug_info'] = debug_info
        
        # Determine if we should fail
        if errors and not edited_policies:
            module.fail_json(msg=f"Security policy editing failed with {len(errors)} error(s). See response.errors for details.", **result)
        elif errors:
            module.exit_json(msg=f"Security policy editing completed with {len(errors)} error(s). See response.errors for details.", **result)
        else:
            module.exit_json(**result)
            
    except Exception as e:
        debug_info['error'] = f"Security policy editing failed: {str(e)}"
        result['debug_info'] = debug_info
        module.fail_json(msg=f"Security policy editing failed: {str(e)}", **result)

def map_security_policy_parameters(policy):
    """Map user-friendly parameter values to API values for security policies."""
    
    # User-friendly mappings based on DefensePro API specifications
    DIRECTION_MAP = {
        'oneway': '1', 'one_way': '1', 'one-way': '1',
        'twoway': '2', 'two_way': '2', 'two-way': '2', 'bidirectional': '2', 'both': '2'
    }
    
    STATE_MAP = {
        'enable': '1', 'enabled': '1', 'active': '1', 'on': '1',
        'disable': '2', 'disabled': '2', 'inactive': '2', 'off': '2'
    }
    
    ACTION_MAP = {
        'report_only': '0', 'report': '0',
        'block_and_report': '1', 'block': '1'
    }
    
    PACKET_REPORTING_MAP = {
        'enable': '1', 'enabled': '1', 'on': '1',
        'disable': '2', 'disabled': '2', 'off': '2'
    }
    
    # Only map values that are explicitly provided by user
    result = {}
    
    # Direction - only map if provided
    if 'direction' in policy and policy['direction'] is not None:
        direction_value = str(policy['direction']).lower()
        result['direction'] = DIRECTION_MAP.get(direction_value, '1')
    
    # State - only map if provided  
    if 'state' in policy and policy['state'] is not None:
        state_value = str(policy['state']).lower()
        result['state'] = STATE_MAP.get(state_value, '1')
    
    # Action - only map if provided
    if 'action' in policy and policy['action'] is not None:
        action_value = str(policy['action']).lower()
        result['action'] = ACTION_MAP.get(action_value, '1')
    
    # Packet reporting - only map if provided
    if 'packet_reporting_status' in policy and policy['packet_reporting_status'] is not None:
        packet_reporting_value = str(policy['packet_reporting_status']).lower()
        result['packet_reporting_status'] = PACKET_REPORTING_MAP.get(packet_reporting_value, '2')
    
    return result

def main():
    run_module()

if __name__ == '__main__':
    main()