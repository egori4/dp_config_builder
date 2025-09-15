# plugins/modules/create_bdos_profile.py
"""
Unified Ansible module to create BDOS profiles on DefensePro devices.

This module follows the same unified architecture pattern as create_security_policy.py.
- Accepts a list of BDoS profiles to create in a single/multiple device.
- Supports check mode, logging, error handling, and parameter mapping with inline validation.
"""

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        bdos_profiles=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # Extract provider and params
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    bdos_profiles = module.params['bdos_profiles']

    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    debug_info['input'] = {
        'dp_ip': dp_ip,
        'profiles_count': len(bdos_profiles)
    }

    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'],
                       provider['password'], log_level=log_level, logger=logger)

        changes_made = False
        created_profiles = []
        errors = []

        if module.check_mode:
            if bdos_profiles:
                planned_operations = [
                    {
                        'profile_name': profile.get('name', 'unnamed_profile'),
                        'params': profile.get('params', {})
                    }
                    for profile in bdos_profiles
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
                        'message': 'No BDoS profiles configured for creation'
                    }
                })

        else:
            if bdos_profiles:
                logger.info(f"Creating {len(bdos_profiles)} BDoS profiles on {dp_ip}")

                for profile in bdos_profiles:
                    profile_name = profile.get('name')
                    if not profile_name:
                        error_msg = "Profile name is required (use 'name' field)"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue

                    # Map params to API format
                    try:
                        api_params = map_netflood_profile_parameters(profile.get('params', {}))
                    except ValueError as e:
                        error_msg = f"Validation failed for profile {profile_name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        continue

                    request_body = {"rsNetFloodProfileName": profile_name}
                    request_body.update(api_params)

                    url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}"

                    logger.info(f"Creating BDoS profile: {profile_name}")
                    logger.debug(f"Request URL: {url}")
                    logger.debug(f"Request body: {request_body}")

                    try:
                        resp = cc._post(url, json=request_body)
                        if resp.status_code in (200, 201):
                            logger.info(f"Successfully created NetFlood profile: {profile_name}")
                            changes_made = True
                            created_profiles.append({
                                'profile_name': profile_name,
                                'status': 'success',
                                'params_applied': api_params
                            })
                        else:
                            error_msg = f"Failed to create NetFlood profile {profile_name}: HTTP {resp.status_code} - {resp.text}"
                            errors.append(error_msg)
                            logger.error(error_msg)

                    except Exception as e:
                        error_msg = f"Error creating NetFlood profile {profile_name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)

            else:
                logger.info(f"No NetFlood profiles configured for creation on {dp_ip}")

            result.update({
                'changed': changes_made,
                'response': {
                    'created_profiles': created_profiles,
                    'errors': errors,
                    'summary': {
                        'successful_profiles': len(created_profiles),
                        'total_profiles_attempted': len(bdos_profiles),
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
                module.fail_json(msg=f"BdoS profile creation completed with {len(errors)} error(s).", **result)

    except Exception as e:
        error_msg = f"BDoS profile creation failed: {str(e)}"
        logger.error(error_msg)
        debug_info['error'] = error_msg
        module.fail_json(msg=error_msg, debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def map_netflood_profile_parameters(params):
    """
    Map user-friendly NetFlood parameters to DefensePro API values.
    """

    ENUM_MAPS = {       
        "syn_flood": {"enable": "1", "disable": "2"},
        "udp_flood": {"enable": "1", "disable": "2"},
        "igmp_flood": {"enable": "1", "disable": "2"},
        "icmp_flood": {"enable": "1", "disable": "2"},
        "tcp_ack_fin_flood": {"enable": "1", "disable": "2"},
        "tcp_rst_flood": {"enable": "1", "disable": "2"},
        "tcp_psh_ack_flood": {"enable": "1", "disable": "2"},
        "tcp_syn_ack_flood": {"enable": "1", "disable": "2"},
        "tcp_frag_flood": {"enable": "1", "disable": "2"},
        "udp_frag_flood": {"enable": "1", "disable": "2"},
        "transparent_optimization": {"enable": "1", "disable": "2"},
        "action": {"report_only": "0", "block_and_report": "1"},
        "burst_attack": {"enable": "1", "disable": "2"},
        "footprint_strictness": {"low": "0", "medium": "1", "high": "2"},
        "bdos_rate_limit": {"disable": "0", "normal_edge": "1", "suspect_edge": "2", "user_defined": "3"},
        "packet_report": {"enable": "1", "disable": "2"},
        "adv_udp_detection": {"enable": "1", "disable": "2"}
    }

    FIELD_MAP = {
        "status": "rsNetFloodProfileStatus",
        "tcp_status": "rsNetFloodProfileTcpStatus",
        "syn_flood": "rsNetFloodProfileTcpSynStatus",
        "udp_flood": "rsNetFloodProfileUdpStatus",
        "igmp_flood": "rsNetFloodProfileIgmpStatus",
        "icmp_flood": "rsNetFloodProfileIcmpStatus",
        "tcp_ack_fin_flood": "rsNetFloodProfileTcpFinAckStatus",
        "tcp_rst_flood": "rsNetFloodProfileTcpRstStatus",
        "tcp_psh_ack_flood": "rsNetFloodProfileTcpPshAckStatus",
        "tcp_syn_ack_flood": "rsNetFloodProfileTcpSynAckStatus",
        "tcp_frag_flood": "rsNetFloodProfileTcpFragStatus",
        "udp_frag_flood": "rsNetFloodProfileUdpFragStatus",

        # Bandwidth / quota
        "inbound_traffic": "rsNetFloodProfileBandwidthIn",
        "outbound_traffic": "rsNetFloodProfileBandwidthOut",
        "tcp_in_quota": "rsNetFloodProfileTcpInQuota",
        "udp_in_quota": "rsNetFloodProfileUdpInQuota",
        "icmp_in_quota": "rsNetFloodProfileIcmpInQuota",
        "igmp_in_quota": "rsNetFloodProfileIgmpInQuota",
        "tcp_out_quota": "rsNetFloodProfileTcpOutQuota",
        "udp_out_quota": "rsNetFloodProfileUdpOutQuota",
        "icmp_out_quota": "rsNetFloodProfileIcmpOutQuota",
        "igmp_out_quota": "rsNetFloodProfileIgmpOutQuota",

        # Other parameters
        "transparent_optimization": "rsNetFloodProfileTransparentOptimization",
        "packet_report": "rsNetFloodProfilePacketReportStatus",
        "action": "rsNetFloodProfileAction",
        "burst_attack": "rsNetFloodProfileBurstEnabled",
        "maximum_interval_between_bursts": "rsNetFloodProfileBurstAttackPeriod",
        "learning_suppression_threshold": "rsNetFloodProfileLearningSuppressionThreshold",
        "footprint_strictness": "rsNetFloodProfileFootprintStrictness",
        "bdos_rate_limit": "rsNetFloodProfileRateLimit",
        "user_defined_rate_limit": "rsNetFloodProfileUserDefinedRateLimit",
        "user_defined_rate_limit_unit": "rsNetFloodProfileUserDefinedRateLimitUnit",
        "adv_udp_detection": "rsNetFloodProfileAdvUdpDetection",
        "udp_excluded_ports": "rsNetFloodProfileUdpExcludedPorts"
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
        if key in ["bandwidth_in", "bandwidth_out"]:
            ivalue = int(value)
            if not (1 <= ivalue <= 1342177280):
                raise ValueError(f"{key} must be between 1 and 1342177280")
            mapped[mapped_key] = str(ivalue)
            continue

        if key.endswith("_in_quota") or key.endswith("_out_quota"):
            ivalue = int(value)
            if not (0 <= ivalue <= 100):
                raise ValueError(f"{key} must be between 0 and 100")
            mapped[mapped_key] = str(ivalue)
            continue

        # User-defined rate limit validation
        if key == "user_defined_rate_limit":
            ivalue = int(value)
            if not (0 <= ivalue <= 400_000_000):
                raise ValueError(f"{key} must be between 0 and 400000000")
            mapped[mapped_key] = str(ivalue)
            continue

        # User-defined rate limit unit validation
        if key == "user_defined_rate_limit_unit":
            UNIT_MAP = {"kbps": "0", "mbps": "1", "gbps": "2"}
            mapped_value = UNIT_MAP.get(str(value).lower())
            if mapped_value is None:
                raise ValueError(f"{key} must be one of {list(UNIT_MAP.keys())}")
            mapped[mapped_key] = mapped_value
            continue

        # learning_suppression_threshold validation (0-50)
        if key == "learning_suppression_threshold":
            ivalue = int(value)
            if not (0 <= ivalue <= 50):
                raise ValueError(f"{key} must be between 0 and 50")
            mapped[mapped_key] = str(ivalue)
            continue

        # Direct mapping (stringified)
        mapped[mapped_key] = str(value)

    return mapped


def main():
    run_module()


if __name__ == '__main__':
    main()
