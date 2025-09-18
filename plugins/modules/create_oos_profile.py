# plugins/modules/create_oos_profile.py
"""
Unified Ansible module to create or manage DefensePro OOS profiles.

- Accepts a list of OOS profiles for creation per device.
- Supports check mode, logging, error handling, and parameter mapping.
- User-friendly enums (enable/disable, actions, risk level) are translated into DefensePro API values.
"""

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        oos_profiles=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    oos_profiles = module.params['oos_profiles']

    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    debug_info['input'] = {
        'dp_ip': dp_ip,
        'profiles_count': len(oos_profiles)
    }

    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'],
                       provider['password'], log_level=log_level, logger=logger)

        changes_made = False
        created_profiles = []
        errors = []

        if module.check_mode:
            planned_operations = [
                {
                    'profile_name': profile.get('name', 'unnamed_profile'),
                    'params': profile.get('params', {})
                }
                for profile in oos_profiles
            ]
            result.update({
                'changed': bool(oos_profiles),
                'response': {
                    'preview_mode': True,
                    'planned_operations': planned_operations
                }
            })
        else:
            if oos_profiles:
                logger.info(f"Creating {len(oos_profiles)} OOS profiles on {dp_ip}")

                for profile in oos_profiles:
                    profile_name = profile.get('name')
                    if not profile_name:
                        error_msg = "Profile name is required (use 'name' field)"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue

                    try:
                        api_params = map_oos_profile_parameters(profile.get('params', {}))
                    except ValueError as e:
                        error_msg = f"Validation failed for profile {profile_name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue

                    request_body = {"rsSTATFULProfileName": profile_name}
                    request_body.update(api_params)

                    url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsStatefulProfileTable/{profile_name}"

                    logger.info(f"Creating OOS profile: {profile_name}")
                    logger.debug(f"Request URL: {url}")
                    logger.debug(f"Request body: {request_body}")

                    try:
                        resp = cc._post(url, json=request_body)
                        if resp.status_code in (200, 201):
                            logger.info(f"Successfully created OOS profile: {profile_name}")
                            changes_made = True
                            created_profiles.append({
                                'profile_name': profile_name,
                                'status': 'success',
                                'params_applied': api_params
                            })
                        else:
                            error_msg = f"Failed to create OOS profile {profile_name}: HTTP {resp.status_code} - {resp.text}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                    except Exception as e:
                        error_msg = f"Error creating OOS profile {profile_name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            else:
                logger.info(f"No OOS profiles configured for creation on {dp_ip}")

            result.update({
                'changed': changes_made,
                'response': {
                    'created_profiles': created_profiles,
                    'errors': errors,
                    'summary': {
                        'successful_profiles': len(created_profiles),
                        'total_profiles_attempted': len(oos_profiles),
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
                module.fail_json(msg=f"OOS profile creation completed with {len(errors)} error(s).", **result)

    except Exception as e:
        error_msg = f"OOS profile creation failed: {str(e)}"
        logger.error(error_msg)
        debug_info['error'] = error_msg
        module.fail_json(msg=error_msg, debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def map_oos_profile_parameters(params):
    """
    Map user-friendly OOS parameters to DefensePro API values.
    Supports enums for enable/disable, actions, and risk levels.
    """

    ENUM_MAPS = {
        "syn_ack_allow": {"enable": "1", "disable": "2"},
        "packet_report": {"enable": "1", "disable": "2"},
        "action": {"report_only": "0", "block_and_report": "1"},
        "risk": {"info": "0", "low": "1", "medium": "2", "high": "3"},
        "idle_state": {"enable": "1", "disable": "2"}
    }

    FIELD_MAP = {
        "act_threshold": "rsSTATFULProfileactThreshold",
        "term_threshold": "rsSTATFULProfiletermThreshold",
        "syn_ack_allow": "rsSTATFULProfilesynAckAllow",
        "packet_report": "rsSTATFULProfilePacketReportStatus",
        "action": "rsSTATFULProfileAction",
        "risk": "rsSTATFULProfileRisk",
        "idle_state": "rsSTATFULProfileEnableIdleState",
        "idle_state_bandwidth_threshold": "rsSTATFULProfileIdleStateBandwidthThreshold",
        "idle_state_timer": "rsSTATFULProfileIdleStateTimer"
    }

    mapped = {}
    for key, value in params.items():
        if key not in FIELD_MAP:
            continue
        mapped_key = FIELD_MAP[key]
        if key in ENUM_MAPS:
            mapped_value = ENUM_MAPS[key].get(str(value).lower())
            if mapped_value is None:
                raise ValueError(f"Invalid enum value '{value}' for {key}. Allowed: {list(ENUM_MAPS[key].keys())}")
            mapped[mapped_key] = mapped_value
        else:
            mapped[mapped_key] = str(value)

    return mapped


def main():
    run_module()


if __name__ == '__main__':
    main()
