# plugins/modules/create_full_config.py
"""
Unified Ansible module to create DefensePro security policies with profile bindings via Radware CyberController API.

This module handles creation of security policies and binding of various protection profiles in a single operation.
Follows the unified architecture pattern established in other modules.
"""

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        security_policies=dict(type='list', required=False, default=[])
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Extract provider and setup logging
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    security_policies = module.params['security_policies']
    
    log_level = provider.get('log_level', 'disabled')
    
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    debug_info['input'] = {
        'dp_ip': dp_ip,
        'policies_count': len(security_policies)
    }
    
    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        changes_made = False
        created_policies = []
        errors = []
        
        if module.check_mode:
            # Check mode - simplified preview
            if security_policies:
                planned_operations = [
                    {
                        'policy_name': policy.get('policy_name', 'unnamed_policy'),
                        'src_network': policy.get('src_network', 'any'),
                        'dst_network': policy.get('dst_network', 'any'),
                        'connection_limit_profile': policy.get('connection_limit_profile', ''),
                        'bdos_profile': policy.get('bdos_profile', ''),
                        'dns_flood_profile': policy.get('dns_flood_profile', ''),
                        'https_flood_profile': policy.get('https_flood_profile', ''),
                        'signature_protection_profile': policy.get('signature_protection_profile', ''),
                        'ert_attackers_feed_profile': policy.get('ert_attackers_feed_profile', ''),
                        'geo_feed_profile': policy.get('geo_feed_profile', ''),
                        'out_of_state_profile': policy.get('out_of_state_profile', '')
                    }
                    for policy in security_policies
                ]
                result.update({
                    'changed': True,
                    'response': {
                        'preview_mode': True,
                        'planned_operations': planned_operations
                    }
                })
            else:
                result.update({
                    'changed': False,
                    'response': {
                        'preview_mode': True,
                        'message': 'No security policies configured for creation'
                    }
                })
                
        else:
            # Actual execution mode
            if security_policies:
                logger.info(f"Creating {len(security_policies)} security policies on {dp_ip}")
                
                for policy in security_policies:
                    policy_name = policy.get('policy_name')
                    if not policy_name:
                        error_msg = "Policy name is required (use 'policy_name' field)"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue
                    
                    # Map user-friendly values to API values (only for provided parameters)
                    api_params = map_security_policy_parameters(policy)
                    
                    # Construct API request body with only policy name as mandatory
                    request_body = {
                        "rsIDSNewRulesName": policy_name
                    }
                    
                    # Add optional parameters only if specified by user
                    if 'src_network' in policy and policy['src_network'] is not None:
                        request_body["rsIDSNewRulesSource"] = policy['src_network']
                    
                    if 'dst_network' in policy and policy['dst_network'] is not None:
                        request_body["rsIDSNewRulesDestination"] = policy['dst_network']
                    
                    # Use mapped values for the following parameters if they were provided
                    if 'direction' in api_params:
                        request_body["rsIDSNewRulesDirection"] = api_params['direction']
                    
                    if 'state' in api_params:
                        request_body["rsIDSNewRulesState"] = api_params['state']
                    
                    if 'action' in api_params:
                        request_body["rsIDSNewRulesAction"] = api_params['action']
                    
                    if 'packet_reporting_status' in api_params:
                        request_body["rsIDSNewRulesPacketReportingStatus"] = api_params['packet_reporting_status']
                    
                    if 'priority' in policy and policy['priority'] is not None:
                        request_body["rsIDSNewRulesPriority"] = str(policy['priority'])
                    
                    # Add profile bindings (only non-empty values)
                    profile_mappings = {
                        "rsIDSNewRulesProfileAppsec": policy.get('signature_protection_profile', ''),
                        "rsIDSNewRulesProfileConlmt": policy.get('connection_limit_profile', ''),
                        "rsIDSNewRulesProfileNetflood": policy.get('bdos_profile', ''),
                        "rsIDSNewRulesProfileSynprotection": policy.get('syn_protection_profile', ''),
                        "rsIDSNewRulesProfileDNS": policy.get('dns_flood_profile', ''),
                        "rsIDSNewRulesProfileHttpsflood": policy.get('https_flood_profile', ''),
                        "rsIDSNewRulesProfileErtAttackersFeed": policy.get('ert_attackers_feed_profile', ''),
                        "rsIDSNewRulesProfileTrafficFilters": policy.get('traffic_filters_profile', ''),
                        "rsIDSNewRulesProfileGeoFeed": policy.get('geo_feed_profile', ''),
                        "rsIDSNewRulesProfileStateful": policy.get('out_of_state_profile', '')
                    }
                    
                    for key, value in profile_mappings.items():
                        if value and value.strip():
                            request_body[key] = value
                    
                    # Create policy
                    url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable/{policy_name}"
                    
                    logger.info(f"Creating security policy: {policy_name}")
                    logger.debug(f"Request URL: {url}")
                    logger.debug(f"Request body: {request_body}")
                    
                    try:
                        resp = cc._post(url, json=request_body)
                        
                        if resp.status_code == 200:
                            logger.info(f"Successfully created security policy: {policy_name}")
                            changes_made = True
                            
                            policy_result = {
                                'policy_name': policy_name,
                                'src_network': policy.get('src_network', 'any'),
                                'dst_network': policy.get('dst_network', 'any'),
                                'direction': policy.get('direction', 'oneway'),
                                'connection_limit_profile': policy.get('connection_limit_profile', ''),
                                'bdos_profile': policy.get('bdos_profile', ''),
                                'dns_flood_profile': policy.get('dns_flood_profile', ''),
                                'https_flood_profile': policy.get('https_flood_profile', ''),
                                'signature_protection_profile': policy.get('signature_protection_profile', ''),
                                'ert_attackers_feed_profile': policy.get('ert_attackers_feed_profile', ''),
                                'geo_feed_profile': policy.get('geo_feed_profile', ''),
                                'out_of_state_profile': policy.get('out_of_state_profile', ''),
                                'status': 'success'
                            }
                            
                            # Only include priority in result if it was specified
                            if 'priority' in policy and policy['priority'] is not None:
                                policy_result['priority'] = policy['priority']
                                
                            created_policies.append(policy_result)
                        else:
                            error_msg = f"Failed to create security policy {policy_name}: HTTP {resp.status_code} - {resp.text}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                            
                    except Exception as e:
                        error_msg = f"Error creating security policy {policy_name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            else:
                logger.info(f"No security policies configured for creation on {dp_ip}")
            
            # Prepare results
            result.update({
                'changed': changes_made,
                'response': {
                    'created_policies': created_policies,
                    'errors': errors,
                    'summary': {
                        'successful_policies': len(created_policies),
                        'total_policies_attempted': len(security_policies),
                        'errors_count': len(errors)
                    }
                }
            })
            
            debug_info['summary'] = {
                'policies_created': len(created_policies),
                'policies_failed': len(errors),
                'operations_completed': changes_made
            }
            
            # Fail the task if there were any errors
            if errors:
                error_msg = f"Security policy creation completed with {len(errors)} error(s). See response.errors for details."
                module.fail_json(msg=error_msg, **result)
    
    except Exception as e:
        error_msg = f"Security policy creation failed: {str(e)}"
        logger.error(error_msg)
        debug_info['error'] = error_msg
        module.fail_json(msg=error_msg, debug_info=debug_info, **result)
    
    result['debug_info'] = debug_info
    module.exit_json(**result)

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
