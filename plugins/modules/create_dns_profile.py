# plugins/modules/create_dns_profile.py
"""
Unified Ansible module to create DNS Protection profiles on DefensePro devices.

Supports check mode, logging, error handling, and detailed debug info.
Provides user-friendly summary mapping API fields to human-readable names.
"""

from ansible.module_utils.basic import AnsibleModule

# Reverse mapping for user-friendly field names
REVERSE_FIELD_MAP = {
    "rsDnsProtProfileAction": "action",
    "rsDnsProtProfileDnsAStatus": "a_status",
    "rsDnsProtProfileDnsMxStatus": "mx_status",
    "rsDnsProtProfileDnsPtrStatus": "ptr_status",
    "rsDnsProtProfileDnsAaaaStatus": "aaaa_status",
    "rsDnsProtProfileDnsTextStatus": "text_status",
    "rsDnsProtProfileDnsSoaStatus": "soa_status",
    "rsDnsProtProfileDnsNaptrStatus": "naptr_status",
    "rsDnsProtProfileDnsSrvStatus": "srv_status",
    "rsDnsProtProfileDnsOtherStatus": "other_status",
    "rsDnsProtProfileExpectedQps": "expected_qps",
    "rsDnsProtProfileMaxAllowQps": "max_allow_qps",
    "rsDnsProtProfileDnsAQuota": "a_quota",
    "rsDnsProtProfileDnsMxQuota": "mx_quota",
    "rsDnsProtProfileDnsPtrQuota": "ptr_quota",
    "rsDnsProtProfileDnsAaaaQuota": "aaaa_quota",
    "rsDnsProtProfileDnsTextQuota": "text_quota",
    "rsDnsProtProfileDnsSoaQuota": "soa_quota",
    "rsDnsProtProfileDnsNaptrQuota": "naptr_quota",
    "rsDnsProtProfileDnsSrvQuota": "srv_quota",
    "rsDnsProtProfileDnsOtherQuota": "other_quota",
    "rsDnsProtProfileFootprintStrictness": "footprint_strictness",
    "rsDnsProtProfileManualTriggerStatus": "manual_trigger",
    "rsDnsProtProfileManualTriggerActThresh": "manual_trigger_act_thresh",
    "rsDnsProtProfileManualTriggerTermThresh": "manual_trigger_term_thresh",
    "rsDnsProtProfileManualTriggerMaxQpsTarget": "manual_trigger_max_qps_target",
    "rsDnsProtProfileManualTriggerActPeriod": "manual_trigger_act_period",
    "rsDnsProtProfileManualTriggerTermPeriod": "manual_trigger_term_period",
    "rsDnsProtProfileManualTriggerEscalatePeriod": "manual_trigger_escalate_period",
    "rsDnsProtProfilePacketReportStatus": "packet_report",
    "rsDnsProtProfileSigRateLimTarget": "sig_rate_lim_target",
    "rsDnsProtProfileQueryNameMonitoringSensitivity": "query_name_sensitivity",
    "rsDnsProtProfileSubdomainsWLLearningState": "subdomains_allow_list",
    "rsDnsProtProfileLearningSuppressionThreshold": "learning_suppression_threshold"
}

# Reverse mapping for enum values
REVERSE_ENUM_MAPS = {
    "rsDnsProtProfileAction": {"0": "report_only", "1": "block_&_report"},
    "rsDnsProtProfileManualTriggerStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfilePacketReportStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileSubdomainsWLLearningState": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileFootprintStrictness": {"0": "low", "1": "medium", "2": "high"},
    "rsDnsProtProfileDnsAStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsMxStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsPtrStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsAaaaStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsTextStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsSoaStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsNaptrStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsSrvStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsOtherStatus": {"1": "enable", "2": "disable"}
}

def map_api_values_to_user_friendly(api_params):
    """Convert numeric API values to human-friendly enums."""
    user_friendly = {}
    for k, v in api_params.items():
        name = REVERSE_FIELD_MAP.get(k, k)
        if k in REVERSE_ENUM_MAPS:
            user_friendly[name] = REVERSE_ENUM_MAPS[k].get(str(v), v)
        else:
            user_friendly[name] = v
    return user_friendly

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        dns_profiles=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    dns_profiles = module.params['dns_profiles']

    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    debug_info['input'] = {'dp_ip': dp_ip, 'profiles_count': len(dns_profiles)}
    logger.debug(f"Module input parameters: {module.params}")

    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'],
                       provider['password'], log_level=log_level, logger=logger)

        changes_made = False
        created_profiles = []
        errors = []

        if module.check_mode:
            planned_ops = [
                {'profile_name': p.get('name', 'unnamed_profile'), 'params': p.get('params', {})}
                for p in dns_profiles
            ] if dns_profiles else []
            result.update({
                'changed': bool(planned_ops),
                'response': {
                    'preview_mode': True,
                    'planned_operations': planned_ops,
                    'message': 'No DNS profiles configured for creation' if not planned_ops else ''
                }
            })

        else:
            if dns_profiles:
                logger.info(f"Creating {len(dns_profiles)} DNS profiles on {dp_ip}")

                for profile in dns_profiles:
                    profile_name = profile.get('name')
                    if not profile_name:
                        err = "Profile name is required (use 'name' field)"
                        errors.append(err)
                        logger.error(err)
                        continue

                    try:
                        api_params = map_dns_profile_parameters(profile.get('params', {}))
                    except ValueError as e:
                        err = f"Validation failed for profile {profile_name}: {str(e)}"
                        errors.append(err)
                        logger.error(err)
                        continue

                    url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}"

                    try:
                        logger.info(f"Creating profile {profile_name}")
                        logger.debug(f"POST URL: {url}")
                        logger.debug(f"POST body: {api_params}")
                        resp = cc._post(url, json={"rsDnsProtProfileName": profile_name, **api_params})
                        if resp.status_code not in (200, 201):
                            err = f"Error creating profile {profile_name}: HTTP {resp.status_code} - {resp.text}"
                            errors.append(err)
                            logger.error(err)
                            continue
                    except Exception as e:
                        err = f"Exception for profile {profile_name}: {str(e)}"
                        errors.append(err)
                        logger.error(err)
                        continue

                    changes_made = True
                    created_profiles.append({
                        'profile_name': profile_name,
                        'status': 'success',
                        'params_applied': api_params,
                        'user_friendly': map_api_values_to_user_friendly(api_params)
                    })

            result.update({
                'changed': changes_made,
                'response': {
                    'created_profiles': created_profiles,
                    'errors': errors,
                    'summary': {
                        'successful_profiles': len(created_profiles),
                        'total_profiles_attempted': len(dns_profiles),
                        'errors_count': len(errors)
                    }
                }
            })

            debug_info['summary'] = {
                'profiles_created': len(created_profiles),
                'profiles_failed': len(errors),
                'operations_completed': changes_made
            }

            if errors:
                module.fail_json(msg=f"DNS profile creation completed with {len(errors)} error(s).", **result)

    except Exception as e:
        err = f"DNS profile creation failed: {str(e)}"
        logger.error(err)
        debug_info['error'] = err
        module.fail_json(msg=err, debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def map_dns_profile_parameters(params):
    """Map user-friendly DNS parameters to DefensePro API values."""
    ENUM_MAPS = {
        "action": {"report_only": "0", "block_&_report": "1"},
        "manual_trigger": {"enable": "1", "disable": "2"},
        "packet_report": {"enable": "1", "disable": "2"},
        "packet_trace": {"enable": "1", "disable": "2"},
        "subdomains_allow_list": {"enable": "1", "disable": "2"},
        "footprint_strictness": {"low": "0", "medium": "1", "high": "2"},
        "a_status": {"enable": "1", "disable": "2"},
        "mx_status": {"enable": "1", "disable": "2"},
        "ptr_status": {"enable": "1", "disable": "2"},
        "aaaa_status": {"enable": "1", "disable": "2"},
        "text_status": {"enable": "1", "disable": "2"},
        "soa_status": {"enable": "1", "disable": "2"},
        "naptr_status": {"enable": "1", "disable": "2"},
        "srv_status": {"enable": "1", "disable": "2"},
        "other_status": {"enable": "1", "disable": "2"}
    }

    FIELD_MAP = {
        "expected_qps": "rsDnsProtProfileExpectedQps",
        "max_allow_qps": "rsDnsProtProfileMaxAllowQps",
        "a_quota": "rsDnsProtProfileDnsAQuota",
        "mx_quota": "rsDnsProtProfileDnsMxQuota",
        "ptr_quota": "rsDnsProtProfileDnsPtrQuota",
        "aaaa_quota": "rsDnsProtProfileDnsAaaaQuota",
        "text_quota": "rsDnsProtProfileDnsTextQuota",
        "soa_quota": "rsDnsProtProfileDnsSoaQuota",
        "naptr_quota": "rsDnsProtProfileDnsNaptrQuota",
        "srv_quota": "rsDnsProtProfileDnsSrvQuota",
        "other_quota": "rsDnsProtProfileDnsOtherQuota",
        "a_status": "rsDnsProtProfileDnsAStatus",
        "mx_status": "rsDnsProtProfileDnsMxStatus",
        "ptr_status": "rsDnsProtProfileDnsPtrStatus",
        "aaaa_status": "rsDnsProtProfileDnsAaaaStatus",
        "text_status": "rsDnsProtProfileDnsTextStatus",
        "soa_status": "rsDnsProtProfileDnsSoaStatus",
        "naptr_status": "rsDnsProtProfileDnsNaptrStatus",
        "srv_status": "rsDnsProtProfileDnsSrvStatus",
        "other_status": "rsDnsProtProfileDnsOtherStatus",
        "action": "rsDnsProtProfileAction",
        "manual_trigger": "rsDnsProtProfileManualTriggerStatus",
        "manual_trigger_act_thresh": "rsDnsProtProfileManualTriggerActThresh",
        "manual_trigger_term_thresh": "rsDnsProtProfileManualTriggerTermThresh",
        "manual_trigger_max_qps_target": "rsDnsProtProfileManualTriggerMaxQpsTarget",
        "manual_trigger_act_period": "rsDnsProtProfileManualTriggerActPeriod",
        "manual_trigger_term_period": "rsDnsProtProfileManualTriggerTermPeriod",
        "manual_trigger_escalate_period": "rsDnsProtProfileManualTriggerEscalatePeriod",
        "packet_report": "rsDnsProtProfilePacketReportStatus",
        "sig_rate_lim_target": "rsDnsProtProfileSigRateLimTarget",
        "query_name_sensitivity": "rsDnsProtProfileQueryNameMonitoringSensitivity",
        "subdomains_allow_list": "rsDnsProtProfileSubdomainsWLLearningState",
        "learning_suppression_threshold": "rsDnsProtProfileLearningSuppressionThreshold",
        "footprint_strictness": "rsDnsProtProfileFootprintStrictness"
    }

    mapped = {}
    for key, value in params.items():
        if key not in FIELD_MAP:
            continue
        mapped_key = FIELD_MAP[key]

        if key in ENUM_MAPS:
            mapped_value = ENUM_MAPS[key].get(str(value).lower())
            if mapped_value is None:
                raise ValueError(f"Invalid value '{value}' for {key}. Allowed: {list(ENUM_MAPS[key].keys())}")
            mapped[mapped_key] = mapped_value
        else:
            mapped[mapped_key] = str(value)

    return mapped

def main():
    run_module()

if __name__ == '__main__':
    main()
