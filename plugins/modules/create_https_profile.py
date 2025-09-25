# plugins/modules/create_https_flood_profile.py
"""
Unified Ansible module to create HTTPS Flood profiles on DefensePro devices.

Supports check mode, logging, error handling, and detailed debug info.
Provides user-friendly summary mapping API fields to human-readable names.
"""

from ansible.module_utils.basic import AnsibleModule

# Reverse mapping for user-friendly field names
REVERSE_FIELD_MAP = {
    "rsHttpsFloodProfileAction": "action",
    "rsHttpsFloodProfileRateLimit": "rate_limit",
    "rsHttpsFloodProfileSelectiveChallenge": "https_authentication_on_suspect_sources",
    "rsHttpsFloodProfileCollectiveChallenge": "https_authentication_on_all_sources",
    "rsHttpsFloodProfileChallengeMethod": "challenge_method",
    "rsHttpsFloodProfileRateLimitStatus": "rate_limit_status",
    "rsHttpsFloodProfilePacketReporting": "packet_report",
    "rsHttpsFloodProfileFullSessionDecryption": "full_session_decryption"
}

# Reverse mapping for enum values
REVERSE_ENUM_MAPS = {
    "rsHttpsFloodProfileAction": {"0": "report_only", "1": "block_and_report"},
    "rsHttpsFloodProfileSelectiveChallenge": {"1": "enable", "2": "disable"},
    "rsHttpsFloodProfileCollectiveChallenge": {"1": "enable", "2": "disable"},
    "rsHttpsFloodProfileChallengeMethod": {"1": "redirect_302", "2": "javascript"},
    "rsHttpsFloodProfileRateLimitStatus": {"1": "enable", "2": "disable"},
    "rsHttpsFloodProfilePacketReporting": {"1": "enable", "2": "disable"},
    "rsHttpsFloodProfileFullSessionDecryption": {"1": "enable", "2": "disable"},
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
        https_flood_profiles=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    https_flood_profiles = module.params['https_flood_profiles']

    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    debug_info['input'] = {'dp_ip': dp_ip, 'profiles_count': len(https_flood_profiles)}

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
                for p in https_flood_profiles
            ] if https_flood_profiles else []
            result.update({
                'changed': bool(planned_ops),
                'response': {
                    'preview_mode': True,
                    'planned_operations': planned_ops,
                    'message': 'No HTTPS Flood profiles configured for creation' if not planned_ops else ''
                }
            })

        else:
            if https_flood_profiles:
                logger.info(f"Creating {len(https_flood_profiles)} HTTPS Flood profiles on {dp_ip}")

                for profile in https_flood_profiles:
                    profile_name = profile.get('name')
                    if not profile_name:
                        err = "Profile name is required (use 'name' field)"
                        errors.append(err)
                        logger.error(err)
                        continue

                    try:
                        api_params = map_https_flood_profile_parameters(profile.get('params', {}))
                    except ValueError as e:
                        err = f"Validation failed for profile {profile_name}: {str(e)}"
                        errors.append(err)
                        logger.error(err)
                        continue

                    url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsHttpsFloodProfileTable/{profile_name}"


                    # Try with all params first
                    logger.info(f"Creating profile {profile_name}")
                    logger.debug(f"POST URL: {url}")
                    logger.debug(f"POST body: {api_params}")
                    try:
                        resp = cc._post(url, json={"rsHttpsFloodProfileName": profile_name, **api_params})
                        if resp.status_code in (200, 201):
                            changes_made = True
                            created_profiles.append({
                                'profile_name': profile_name,
                                'status': 'success',
                                'params_applied': api_params,
                                'user_friendly': map_api_values_to_user_friendly(api_params)
                            })
                            continue
                        # If error, check for unsupported key in response
                        resp_json = resp.json() if resp.content else {}
                        error_message = resp_json.get('message', '')
                        logger.debug(f"Error message is {error_message}")
                        raise Exception(error_message or f"HTTP {resp.status_code} - {resp.text}")
                    except Exception as e:
                        err_msg = str(e)
                        logger.debug(f"Exception message: {err_msg}")
                        if 'rsHttpsFloodProfilePacketReporting' in err_msg:
                            logger.warning(f"Key rsHttpsFloodProfilePacketReporting not supported, retrying without it for {profile_name}")
                            api_params_wo_packet_report = dict(api_params)
                            api_params_wo_packet_report.pop('rsHttpsFloodProfilePacketReporting', None)
                            try:
                                resp2 = cc._post(url, json={"rsHttpsFloodProfileName": profile_name, **api_params_wo_packet_report})
                                if resp2.status_code in (200, 201):
                                    changes_made = True
                                    created_profiles.append({
                                        'profile_name': profile_name,
                                        'status': 'success',
                                        'params_applied': api_params_wo_packet_report,
                                        'user_friendly': map_api_values_to_user_friendly(api_params_wo_packet_report)
                                    })
                                    logger.info(f"Creating profile {profile_name}")
                                    logger.debug(f"POST URL: {url}")
                                    logger.debug(f"POST body: {api_params_wo_packet_report}")
                                    logger.debug(f"Response: {resp2.json()}")
                                    logger.info(f"Successfully created profile {profile_name} without packet_report")
                                    continue
                                else:
                                    err = f"Error creating profile {profile_name} (retry without packet_report): HTTP {resp2.status_code} - {resp2.text}"
                                    errors.append(err)
                                    logger.error(err)
                                    continue
                            except Exception as e2:
                                err = f"Exception for profile {profile_name} (retry without packet_report): {str(e2)}"
                                errors.append(err)
                                logger.error(err)
                                continue
                        else:
                            err = f"Error creating profile {profile_name}: {err_msg}"
                            errors.append(err)
                            logger.error(err)
                            continue

            result.update({
                'changed': changes_made,
                'response': {
                    'created_profiles': created_profiles,
                    'errors': errors,
                    'summary': {
                        'successful_profiles': len(created_profiles),
                        'total_profiles_attempted': len(https_flood_profiles),
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
                module.fail_json(msg=f"HTTPS Flood profile creation completed with {len(errors)} error(s).", **result)

    except Exception as e:
        err = f"HTTPS Flood profile creation failed: {str(e)}"
        logger.error(err)
        debug_info['error'] = err
        module.fail_json(msg=err, debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def map_https_flood_profile_parameters(params):
    """Map user-friendly HTTPS Flood parameters to DefensePro API values."""
    ENUM_MAPS = {
        "action": {"report_only": "0", "block_and_report": "1"},
        "https_authentication_on_suspect_sources": {"enable": "1", "disable": "2"},
        "https_authentication_on_all_sources": {"enable": "1", "disable": "2"},
        "challenge_method": {"redirect_302": "1", "javascript": "2"},
        "rate_limit_status": {"enable": "1", "disable": "2"},
        "packet_report": {"enable": "1", "disable": "2"},
        "full_session_decryption": {"enable": "1", "disable": "2"}
    }

    FIELD_MAP = {
        "action": "rsHttpsFloodProfileAction",
        "rate_limit": "rsHttpsFloodProfileRateLimit",
        "https_authentication_on_suspect_sources": "rsHttpsFloodProfileSelectiveChallenge",
        "https_authentication_on_all_sources": "rsHttpsFloodProfileCollectiveChallenge",
        "challenge_method": "rsHttpsFloodProfileChallengeMethod",
        "rate_limit_status": "rsHttpsFloodProfileRateLimitStatus",
        "packet_report": "rsHttpsFloodProfilePacketReporting",
        "full_session_decryption": "rsHttpsFloodProfileFullSessionDecryption"
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
