# plugins/modules/create_bdos_profile.py
"""
Unified Ansible module to create BDOS profiles on DefensePro devices with two-phase execution.

Phase 1: Create profile + apply bandwidth and core parameters (POST)
Phase 2: Update quotas (PUT), only if Phase 1 succeeded or bandwidth already exists

Supports check mode, logging, error handling, and detailed debug info.
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

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    bdos_profiles = module.params['bdos_profiles']

    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    debug_info['input'] = {'dp_ip': dp_ip, 'profiles_count': len(bdos_profiles)}

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
                for p in bdos_profiles
            ] if bdos_profiles else []
            result.update({
                'changed': bool(planned_ops),
                'response': {
                    'preview_mode': True,
                    'planned_operations': planned_ops,
                    'message': 'No BDoS profiles configured for creation' if not planned_ops else ''
                }
            })

        else:
            if bdos_profiles:
                logger.info(f"Creating {len(bdos_profiles)} BDoS profiles on {dp_ip}")

                for profile in bdos_profiles:
                    profile_name = profile.get('name')
                    if not profile_name:
                        err = "Profile name is required (use 'name' field)"
                        errors.append(err)
                        logger.error(err)
                        continue

                    try:
                        api_params = map_netflood_profile_parameters(profile.get('params', {}))
                    except ValueError as e:
                        err = f"Validation failed for profile {profile_name}: {str(e)}"
                        errors.append(err)
                        logger.error(err)
                        continue

                    # Split Phase 1 vs Phase 2
                    phase1_keys = [
                        "rsNetFloodProfileAction", "rsNetFloodProfileAdvUdpDetection",
                        "rsNetFloodProfileBandwidthIn", "rsNetFloodProfileBandwidthOut",
                        "rsNetFloodProfileBurstEnabled", "rsNetFloodProfileBurstAttackPeriod",
                        "rsNetFloodProfileFootprintStrictness", "rsNetFloodProfileLearningSuppressionThreshold",
                        "rsNetFloodProfilePacketReportStatus", "rsNetFloodProfileTcpSynStatus",
                        "rsNetFloodProfileTcpRstStatus", "rsNetFloodProfileTcpSynAckStatus",
                        "rsNetFloodProfileTcpFinAckStatus", "rsNetFloodProfileTcpFragStatus",
                        "rsNetFloodProfileUdpStatus", "rsNetFloodProfileUdpFragStatus",
                        "rsNetFloodProfileIgmpStatus", "rsNetFloodProfileIcmpStatus",
                        "rsNetFloodProfileTransparentOptimization",
                        "rsNetFloodProfileRateLimit", "rsNetFloodProfileUserDefinedRateLimit",
                        "rsNetFloodProfileUserDefinedRateLimitUnit"
                    ]

                    phase1_params = {k: v for k, v in api_params.items() if k in phase1_keys}
                    phase2_params = {k: v for k, v in api_params.items() if k not in phase1_keys}

                    url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}"

                    # Phase 1: POST
                    try:
                        logger.info(f"[Phase 1] Creating profile {profile_name}")
                        logger.debug(f"POST URL: {url}")
                        logger.debug(f"POST body: {phase1_params}")
                        resp = cc._post(url, json={"rsNetFloodProfileName": profile_name, **phase1_params})
                        if resp.status_code not in (200, 201):
                            err = f"Phase 1 error for profile {profile_name}: HTTP {resp.status_code} - {resp.text}"
                            errors.append(err)
                            logger.error(err)
                            continue
                        logger.info(f"[Phase 1] Success for profile {profile_name}")
                    except Exception as e:
                        err = f"Phase 1 exception for profile {profile_name}: {str(e)}"
                        errors.append(err)
                        logger.error(err)
                        continue

                    # Phase 2: PUT (quotas)
                    try:
                        if phase2_params:
                            logger.info(f"[Phase 2] Applying quotas for profile {profile_name}")
                            logger.debug(f"PUT URL: {url}")
                            logger.debug(f"PUT body: {phase2_params}")
                            resp = cc._put(url, json=phase2_params)
                            if resp.status_code not in (200, 201):
                                err = f"Phase 2 error for profile {profile_name}: HTTP {resp.status_code} - {resp.text}"
                                errors.append(err)
                                logger.error(err)
                            else:
                                logger.info(f"[Phase 2] Quotas applied successfully for {profile_name}")
                    except Exception as e:
                        err = f"Phase 2 exception for profile {profile_name}: {str(e)}"
                        errors.append(err)
                        logger.error(err)

                    changes_made = True
                    created_profiles.append({
                        'profile_name': profile_name,
                        'status': 'success',
                        'params_applied_phase1': phase1_params,
                        'params_applied_phase2': phase2_params
                    })

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
                module.fail_json(msg=f"BDoS profile creation completed with {len(errors)} error(s).", **result)

    except Exception as e:
        err = f"BDoS profile creation failed: {str(e)}"
        logger.error(err)
        debug_info['error'] = err
        module.fail_json(msg=err, debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def map_netflood_profile_parameters(params):
    """Map user-friendly parameters to DefensePro API values."""
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
        "udp_ packet_rate_detection_sensitivit": {"	Ignore_or_Disable":"1","low": "2", "medium": "3", "high": "4"},
        "adv_udp_detection": {"enable": "1", "disable": "2"}
    }

    FIELD_MAP = {
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
        "transparent_optimization": "rsNetFloodProfileTransparentOptimization",
        "action": "rsNetFloodProfileAction",
        "burst_attack": "rsNetFloodProfileBurstEnabled",
        "footprint_strictness": "rsNetFloodProfileFootprintStrictness",
        "bdos_rate_limit": "rsNetFloodProfileRateLimit",
        "packet_report": "rsNetFloodProfilePacketReportStatus",
        "udp_ packet_rate_detection_sensitivit": "rsNetFloodProfileLevelOfReuglarzation",
        "adv_udp_detection": "rsNetFloodProfileAdvUdpDetection",
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
        "maximum_interval_between_bursts": "rsNetFloodProfileNoBurstTimeout",
        "learning_suppression_threshold": "rsNetFloodProfileLearningSuppressionThreshold",
        "user_defined_rate_limit": "rsNetFloodProfileUserDefinedRateLimit",
        "user_defined_rate_limit_unit": "rsNetFloodProfileUserDefinedRateLimitUnit"
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
            continue

        if key in ["inbound_traffic", "outbound_traffic"]:
            ivalue = int(value)
            if not (1 <= ivalue <= 1342177280):
                raise ValueError(f"{key} must be between 1 and 1342177280")
            mapped[mapped_key] = str(ivalue)
            continue

        if key.endswith("_quota"):
            ivalue = int(value)
            if not (0 <= ivalue <= 100):
                raise ValueError(f"{key} must be between 0 and 100")
            mapped[mapped_key] = str(ivalue)
            continue

        if key == "user_defined_rate_limit":
            ivalue = int(value)
            if not (0 <= ivalue <= 400_000_000):
                raise ValueError(f"{key} must be between 0 and 400000000")
            mapped[mapped_key] = str(ivalue)
            continue

        if key == "user_defined_rate_limit_unit":
            UNIT_MAP = {"kbps": "0", "mbps": "1", "gbps": "2"}
            mapped_value = UNIT_MAP.get(str(value).lower())
            if mapped_value is None:
                raise ValueError(f"{key} must be one of {list(UNIT_MAP.keys())}")
            mapped[mapped_key] = mapped_value
            continue

        if key == "learning_suppression_threshold":
            ivalue = int(value)
            if not (0 <= ivalue <= 50):
                raise ValueError(f"{key} must be between 0 and 50")
            mapped[mapped_key] = str(ivalue)
            continue

        mapped[mapped_key] = str(value)

    return mapped

def main():
    run_module()

if __name__ == '__main__':
    main()
