# plugins/modules/format_display.py
"""
Unified Ansible module for formatting and displaying complex output with proper line breaks.
Provides consistent formatting across all playbooks in the DefensePro Configuration Builder.
"""

from ansible.module_utils.basic import AnsibleModule

def format_orchestration_plan(data):
    """Format orchestration plan display."""
    devices = data.get('devices', [])
    config = data.get('config', {})
    policies = data.get('policies', [])
    
    # Show actual count if enabled, 0 if disabled
    policy_count = len(policies) if config.get('create_security_policies', False) else 0
    
    lines = [
        "DefensePro Security Policy Creation Plan:",
        "=" * 42,
        f"Target Device(s): {', '.join(devices)}",
        "Control Flags:",
        f"  - Create Network Classes: {config.get('create_network_classes', False)}",
        f"  - Create CL Profiles: {config.get('create_cl_profiles', False)}",
        f"  - Create Security Policies: {config.get('create_security_policies', False)}",
        f"Security Policies to Create: {policy_count}"
    ]
    
    return lines

def format_policy_summary(data):
    """Format security policy summary display."""
    devices = data.get('devices', [])
    policies = data.get('policies', [])
    config = data.get('config', {})
    
    # Check if security policy creation is enabled
    if not config.get('create_security_policies', False):
        return ["Security policy creation is disabled. No policies will be configured."]
    
    if not policies:
        return ["No security policies configured for creation"]
    
    lines = [f"Creating {len(policies)} security policies on {len(devices)} device(s):"]
    
    for policy in policies:
        policy_name = policy.get('policy_name', 'unnamed')
        src = policy.get('src_network', 'any')
        dst = policy.get('dst_network', 'any')
        priority = policy.get('priority', '100')
        
        lines.append(f"- {policy_name} ({src} -> {dst})")
        lines.append(f"  Priority: {priority}")
        
        # Add profile bindings
        profile_bindings = [
            ('Connection Limit Profile', policy.get('connection_limit_profile', '')),
            ('BDOS Profile', policy.get('bdos_profile', '')),
            ('SYN Protection Profile', policy.get('syn_protection_profile', '')),
            ('DNS Flood Profile', policy.get('dns_flood_profile', '')),
            ('HTTPS Flood Profile', policy.get('https_flood_profile', '')),
            ('Traffic Filters Profile', policy.get('traffic_filters_profile', '')),
            ('Signature Protection Profile', policy.get('signature_protection_profile', '')),
            ('ERT Attackers Feed Profile', policy.get('ert_attackers_feed_profile', '')),
            ('Geo Feed Profile', policy.get('geo_feed_profile', '')),
            ('Out of State Profile', policy.get('out_of_state_profile', ''))
        ]
        
        for profile_name, profile_value in profile_bindings:
            lines.append(f"  {profile_name}: {profile_value}")
    
    return lines

def format_creation_results(data):
    """Format creation results display."""
    device = data.get('device', 'unknown')
    response = data.get('response', {})
    
    lines = [f"Device: {device}"]
    
    if response.get('preview_mode'):
        lines.append("PREVIEW MODE - No actual changes made")
        planned_ops = response.get('planned_operations', [])
        lines.append(f"Planned Operations: {len(planned_ops)}")
        for op in planned_ops:
            lines.append(f"- {op.get('description', 'Unknown operation')}")
    else:
        # Real execution results
        summary = response.get('summary', {})
        total = summary.get('total_policies_attempted', 0)
        successful = summary.get('successful_policies', 0)
        errors_count = summary.get('errors_count', 0)
        
        lines.extend([
            "Security Policy Creation Results:",
            f"Total Attempted: {total}",
            f"Successfully Created: {successful}",
            f"Errors: {errors_count}"
        ])
        
        # Show successful policies
        created_policies = response.get('created_policies', [])
        if created_policies:
            lines.append("")
            lines.append("Successfully Created Policies:")
            for policy in created_policies:
                src = policy.get('src_network', 'any')
                dst = policy.get('dst_network', 'any')
                lines.append(f"- {policy.get('policy_name')} ({src} -> {dst})")
        
        # Show errors
        errors = response.get('errors', [])
        if errors:
            lines.append("")
            lines.append("Errors:")
            for error in errors:
                lines.append(f"- {error}")
    
    return lines

def run_module():
    module_args = dict(
        format_type=dict(
            type='str', 
            required=True, 
            choices=['orchestration_plan', 'policy_summary', 'creation_results']
        ),
        data=dict(type='dict', required=True),
        output_method=dict(
            type='str', 
            default='warn', 
            choices=['warn', 'debug']
        )
    )
    
    result = dict(changed=False)
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    format_type = module.params['format_type']
    data = module.params['data']
    output_method = module.params['output_method']
    
    # Format the data based on type
    formatters = {
        'orchestration_plan': format_orchestration_plan,
        'policy_summary': format_policy_summary,
        'creation_results': format_creation_results
    }
    
    if format_type not in formatters:
        module.fail_json(msg=f"Unknown format_type: {format_type}")
    
    lines = formatters[format_type](data)
    
    # Display the formatted lines
    if output_method == 'warn':
        for line in lines:
            module.warn(line)
    else:  # debug
        for line in lines:
            module.debug(line)
    
    # Return minimal result to reduce JSON output
    module.exit_json(changed=False)

def main():
    run_module()

if __name__ == '__main__':
    main()
