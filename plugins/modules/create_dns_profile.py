# plugins/modules/create_dns_profile.py
"""
Unified Ansible module to create DNS Protection profiles on DefensePro devices.

This module follows the same unified architecture pattern as create_bdos_profile.py.
- Accepts a list of DNS profiles to create in a single/multiple device.
- Supports check mode, logging, error handling, and parameter mapping with inline validation.
"""

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        dns_profiles=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # Extract provider and params
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    dns_profiles = module.params['dns_profiles']

    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    debug_info['input'] = {
        'dp_ip': dp_ip,
        'profiles_count': len(dns_profiles)
    }

    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'],
                       provider['password'], log_level=log_level, logger=logger)

        changes_made = False
        created_profiles = []
        errors = []

        if module.check_mode:
            if dns_profiles:
                planned_operations = [
                    {
                        'profile_name': profile.get('name', 'unnamed_profile'),
                        'params': profile.get('params', {})
                    }
                    for profile in dns_profiles
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
                        'message': 'No DNS profiles configured for creation'
                    }
                })

        else:
            if dns_profiles:
                logger.info(f"Creating {len(dns_profiles)} DNS profiles on {dp_ip}")

                for profile in dns_profiles:
                    profile_name = profile.get('name')
                    if not profile_name:
                        error_msg = "Profile name is required (use 'name' field)"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue

                    # Map params to API format
                    try:
                        api_params = map_dns_profile_parameters(profile.get('params', {}))
                    except ValueError as e:
                        error_msg = f"Validation failed for profile {profile_name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue

                    request_body = {"rsDnsProtProfileName": profile_name}
                    request_body.update(api_params)

                    url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}"

                    logger.info(f"Creating DNS profile: {profile_name}")
                    logger.debug(f"Request URL: {url}")
                    logger.debug(f"Request body: {request_body}")

                    try:
                        resp = cc._post(url, json=request_body)
                        if resp.status_code in (200, 201):
                            logger.info(f"Successfully created DNS profile: {profile_name}")
                            changes_made = True
                            created_profiles.append({
                                'profile_name': profile_name,
                                'status': 'success',
                                'params_applied': api_params
                            })
                        else:
                            error_msg = f"Failed to create DNS profile {profile_name}: HTTP {resp.status_code} - {resp.text}"
                            errors.append(error_msg)
                            logger.error(error_msg)

                    except Exception as e:
                        error_msg = f"Error creating DNS profile {profile_name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)

            else:
                logger.info(f"No DNS profiles configured for creation on {dp_ip}")

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
        error_msg = f"DNS profile creation failed: {str(e)}"
        logger.error(error_msg)
        debug_info['error'] = error_msg
        module.fail_json(msg=error_msg, debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def map_dns_profile_parameters(params):
    """
    Map user-friendly DNS Protection parameters to DefensePro API values.
    """

    ENUM_MAPS = {
        "action": {"report_only": "0", "block_and_report": "1"},
        "manual_trigger": {"enable": "1", "disable": "2"},
        "footprint_strictness": {"low": "0", "medium": "1", "high": "2"},
        "packet_report": {"enable": "1", "disable": "2"}
    }

    FIELD_MAP = {
        "expected_qps": "rsDnsProtProfileExpectedQps",
        "action": "rsDnsProtProfileAction",
        "max_allow_qps": "rsDnsProtProfileMaxAllowQps",
        "manual_trigger": "rsDnsProtProfileManualTriggerStatus",
        "footprint_strictness": "rsDnsProtProfileFootprintStrictness",
        "packet_report": "rsDnsProtProfilePacketReportStatus",
        "learning_suppression_threshold": "rsDnsProtProfileLearningSuppressionThreshold",
        "a_quota": "rsDnsProtProfileDnsAQuota",
        "mx_quota": "rsDnsProtProfileDnsMxQuota",
        "ptr_quota": "rsDnsProtProfileDnsPtrQuota",
        "aaaa_quota": "rsDnsProtProfileDnsAaaaQuota",
        "text_quota": "rsDnsProtProfileDnsTextQuota",
        "soa_quota": "rsDnsProtProfileDnsSoaQuota",
        "DNS Other Quota": "rsDnsProtProfileDnsOtherQuota"

    }

    mapped = {}

    for key, value in params.items():
        if key not in FIELD_MAP:
            continue

        mapped_key = FIELD_MAP[key]

        # Enum mapping
        if key in ENUM_MAPS:
            mapped_value = ENUM_MAPS[key].get(str(value).lower())
            if mapped_value is None:
                raise ValueError(f"Invalid value '{value}' for {key}. Allowed: {list(ENUM_MAPS[key].keys())}")
            mapped[mapped_key] = mapped_value
            continue

        # Range validations
        if key in ["DNS Expected Qps", "DNS Max Allow Qps"]:
            ivalue = int(value)
            if not (0 <= ivalue <= 400000000):
                raise ValueError(f"{key} must be between 0 and 400000000")
            mapped[mapped_key] = str(ivalue)
            continue

        if key == "DNS Learning Suppression Threshold":
            ivalue = int(value)
            if not (0 <= ivalue <= 50):
                raise ValueError(f"{key} must be between 0 and 50")
            mapped[mapped_key] = str(ivalue)
            continue

        # Direct mapping
        mapped[mapped_key] = str(value)

    return mapped


def main():
    run_module()


if __name__ == '__main__':
    main()
