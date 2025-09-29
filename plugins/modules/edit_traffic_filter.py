"""
Unified Ansible module to edit DefensePro Traffic Filter profiles and protections.

Supports updating profile parameters and protection parameters using the same
structure as the create_traffic_filter module for consistency.
"""

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        provider=dict(type="dict", required=True),
        dp_ip=dict(type="str", required=True),
        traffic_filters=dict(type="dict", required=False, default={})
    )

    result = dict(changed=False, response={}, debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params["provider"]
    dp_ip = module.params["dp_ip"]
    traffic_filters = module.params["traffic_filters"]

    profiles = traffic_filters.get("profiles", [])
    protections = traffic_filters.get("protections", [])

    debug_info = {
        "dp_ip": dp_ip,
        "profiles_count": len(profiles),
        "protections_count": len(protections),
    }

    try:
        from ansible.module_utils.logger import Logger
        from ansible.module_utils.radware_cc import RadwareCC

        log_level = provider.get("log_level", "disabled")
        logger = Logger(verbosity=log_level)

        cc = RadwareCC(
            provider["cc_ip"],
            provider["username"],
            provider["password"],
            log_level=log_level,
            logger=logger,
        )

        changes_made = False
        edited_profiles = []
        edited_protections = []

        if not module.check_mode:
            # === Step 1: Edit profiles ===
            for profile in profiles:
                profile_name = profile["name"]
                params = map_profile_parameters(profile.get("params", {}))

                path = f"/mgmt/device/byip/{dp_ip}/config/rsNewTrafficProfileTable/{profile_name}"
                url = f"https://{provider['cc_ip']}{path}"

                logger.info(f"Editing Traffic Filter profile '{profile_name}'")
                resp = cc._put(url, json=params)
                data = resp.json()

                edited_profiles.append({
                    "profile_name": profile_name,
                    "response": data
                })
                changes_made = True

            # === Step 2: Edit protections ===
            for prot in protections:
                profile_name = prot["profile_name"]
                protection_name = prot["name"]
                params = map_protection_parameters(prot.get("params", {}))
                params["rsNewTrafficFilterProfileName"] = profile_name
                params["rsNewTrafficFilterName"] = protection_name

                path = f"/mgmt/device/byip/{dp_ip}/config/rsNewTrafficFilterTable/{profile_name}/{protection_name}"
                url = f"https://{provider['cc_ip']}{path}"

                logger.info(f"Editing Traffic Filter protection '{protection_name}' under profile '{profile_name}'")
                resp = cc._put(url, json=params)
                data = resp.json()

                edited_protections.append({
                    "profile_name": profile_name,
                    "protection_name": protection_name,
                    "response": data
                })
                changes_made = True

        result["changed"] = changes_made
        result["response"] = {
            "edited_profiles": edited_profiles,
            "edited_protections": edited_protections,
        }
        result["debug_info"] = debug_info

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    module.exit_json(**result)


def map_profile_parameters(params):
    """Map user-friendly profile params to API values"""
    ACTION_MAP = {"enable": "1", "disable": "2"}
    return {
        "rsNewTrafficProfileName": params.get("name"),
        "rsNewTrafficProfileAction": ACTION_MAP.get(params.get("action", "enable"), "1"),
    }


def map_protection_parameters(params):
    """Map user-friendly protection params to API values"""
    PACKET_REPORT_MAP = {"enable": "1", "disable": "2"}
    return {
        "rsNewTrafficFilterMatchCriteria": params.get("match_criteria", "1"),
        "rsNewTrafficFilterProtocol": params.get("protocol", "0"),
        "rsNewTrafficFilterThresholdPPS": str(params.get("threshold_pps", "10000")),
        "rsNewTrafficFilterThresholdBPS": str(params.get("threshold_bps", "0")),
        "rsNewTrafficFilterPacketReport": PACKET_REPORT_MAP.get(params.get("packet_report", "enable"), "1"),
        "rsNewTrafficFilterAttackTrackingType": params.get("tracking_type", "0"),
    }


def main():
    run_module()


if __name__ == "__main__":
    main()
