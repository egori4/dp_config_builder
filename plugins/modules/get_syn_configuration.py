"""
Ansible module to fetch DefensePro SYN profiles, protections, and parameters in order: profile → protections → parameters.
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC

FIELD_MAP = {
    "rsIDSSynProfilesAction": "action",
    "rsIDSSynProfileDestinationPorts": "destination_ports",
    "rsIDSSynProfileActivationMode": "activation_mode",
    "rsIDSSynProfileActivationThreshold": "activation_threshold",
    "rsIDSSynProfileTerminationThreshold": "termination_threshold",
    "rsIDSSynProfileTCPResetStatus": "tcp_reset_status",
    "rsIDSSynProfilesParamsAuthType": "auth_type",
}

VALUE_MAPS = {
    "action": {"0": "report_only", "1": "block_and_report"},
    "destination_ports": {"1": "syn_profile", "2": "all"},
    "activation_mode": {"1": "continuous", "2": "threshold_based"},
    "tcp_reset_status": {"1": "enable", "2": "disable"},
    "auth_type": {"1": "safe_reset", "2": "transparent_proxy"},
}


def is_not_applicable(key, params):
    """Report whether a visible DefensePro 10.10.1 control is unavailable."""
    if key == "tcp_reset_status":
        auth_type = str(params.get("auth_type") or "safe_reset").strip().lower()
        return auth_type != "safe_reset"
    return False


def format_syn_params_for_display(raw_profile_params):
    """Convert raw SYN profile parameters to user-friendly format."""
    formatted = {}
    for api_field, user_field in FIELD_MAP.items():
        value = raw_profile_params.get(api_field)
        if value is None or str(value).strip() == "":
            continue

        if user_field in ("activation_threshold", "termination_threshold"):
            try:
                formatted[user_field] = int(value)
            except (TypeError, ValueError):
                formatted[user_field] = value
            continue

        formatted[user_field] = VALUE_MAPS.get(user_field, {}).get(str(value).strip(), value)

    return {
        key: "not_applicable" if is_not_applicable(key, formatted) else formatted.get(key, "N/A")
        for key in FIELD_MAP.values()
    }


def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        filter_syn_profile_names=dict(type='list', required=False, default=[]),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    filter_syn_profile_names = module.params['filter_syn_profile_names']

    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    result = dict(changed=False, profiles=[], protections=[], debug_info={})
    debug_info = {}

    try:
        logger.info("=" * 60)
        cc_ip = provider['cc_ip']
        logger.info(f"Starting SYN configuration fetch for device {dp_ip} on CC {cc_ip}")

        cc = RadwareCC(cc_ip, provider['username'], provider['password'],
                       verify_ssl=provider.get('verify_ssl', False),
                       log_level=log_level, logger=logger)

        # ---------------- Fetch SYN Protections ----------------
        prot_url = f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable"
        logger.info(f"Fetching SYN protections from {dp_ip}")
        logger.debug(f"Request: {{'method': 'GET', 'url': '{prot_url}'}}")
        prot_resp = cc._get(prot_url)
        logger.debug(f"Response status: {prot_resp.status_code}")
        try:
            prot_json = prot_resp.json()
            logger.debug(f"Response JSON: {prot_json}")
        except Exception:
            logger.debug(f"Response text: {prot_resp.text[:500]}")
            prot_json = {}
        syn_protections = prot_json.get('rsIDSSYNAttackTable', [])
        prot_by_name = {p.get('rsIDSSYNAttackName'): p for p in syn_protections}
        result['protections'] = [{
            'protection_name': protection.get('rsIDSSYNAttackName'),
            'protection_id': protection.get('rsIDSSYNAttackId'),
            'activation_threshold': protection.get('rsIDSSYNAttackActivationThreshold'),
            'termination_threshold': protection.get('rsIDSSYNAttackTerminationThreshold'),
            'app_port_group': protection.get('rsIDSSYNDestinationAppPortGroup')
        } for protection in syn_protections]
        debug_info['syn_protections_count'] = len(syn_protections)

        # ---------------- Fetch SYN Profiles ----------------
        prof_url = f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesTable"
        logger.info(f"Fetching SYN profiles from {dp_ip}")
        logger.debug(f"Request: {{'method': 'GET', 'url': '{prof_url}'}}")
        prof_resp = cc._get(prof_url)
        logger.debug(f"Response status: {prof_resp.status_code}")
        try:
            prof_json = prof_resp.json()
            logger.debug(f"Response JSON: {prof_json}")
        except Exception:
            logger.debug(f"Response text: {prof_resp.text[:500]}")
            prof_json = {}
        syn_profiles = prof_json.get('rsIDSSynProfilesTable', [])
        debug_info['syn_profiles_count'] = len(syn_profiles)

        # ---------------- Fetch SYN Profile Parameters ----------------
        params_url = f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesParamsTable"
        logger.info(f"Fetching SYN profile parameters from {dp_ip}")
        logger.debug(f"Request: {{'method': 'GET', 'url': '{params_url}'}}")
        params_resp = cc._get(params_url)
        logger.debug(f"Response status: {params_resp.status_code}")
        try:
            params_json = params_resp.json()
            logger.debug(f"Response JSON: {params_json}")
        except Exception:
            logger.debug(f"Response text: {params_resp.text[:500]}")
            params_json = {}
        syn_profile_params = params_json.get('rsIDSSynProfilesParamsTable', [])
        params_by_name = {p.get('rsIDSSynProfilesParamsName'): p for p in syn_profile_params}
        debug_info['syn_profile_params_count'] = len(syn_profile_params)

        # ---------------- Build structured output ----------------
        all_profiles = []
        profiles_by_name = {}
        for profile in syn_profiles:
            profile_name = profile.get('rsIDSSynProfilesName', 'DEFAULT_PROFILE')
            protection_name = profile.get('rsIDSSynProfileServiceName')

            profile_struct = profiles_by_name.get(profile_name)
            if profile_struct is None:
                profile_struct = {
                    'profile': {'profile_name': profile_name},
                    'protections': [],
                    'parameters': format_syn_params_for_display(params_by_name.get(profile_name, {}))
                }
                profiles_by_name[profile_name] = profile_struct
                all_profiles.append(profile_struct)

            if protection_name:
                prot_details = prot_by_name.get(protection_name, {})
                profile_struct['protections'].append({
                    'protection_name': protection_name,
                    'protection_id': prot_details.get('rsIDSSYNAttackId'),
                    'activation_threshold': prot_details.get('rsIDSSYNAttackActivationThreshold'),
                    'termination_threshold': prot_details.get('rsIDSSYNAttackTerminationThreshold'),
                    'app_port_group': prot_details.get('rsIDSSYNDestinationAppPortGroup')
                })

        # Apply optional filtering
        if filter_syn_profile_names:
            filtered = [p for p in all_profiles if p['profile']['profile_name'] in filter_syn_profile_names]
            result['profiles'] = filtered
            debug_info.update({
                'filter_applied': True,
                'filter_syn_profile_names': filter_syn_profile_names,
                'filtered_count': len(filtered),
                'total_count': len(all_profiles)
            })
        else:
            result['profiles'] = all_profiles
            debug_info.update({
                'filter_applied': False,
                'total_count': len(all_profiles)
            })

        result['debug_info'] = debug_info
        logger.info(f"Completed SYN configuration fetch for {dp_ip}")
        logger.info("=" * 60)
        module.exit_json(**result)

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        logger.info("=" * 60)
        module.fail_json(msg=str(e), debug_info=debug_info or {})

def main():
    run_module()

if __name__ == '__main__':
    main()
