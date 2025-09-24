#!/usr/bin/python
"""
Ansible module to fetch DefensePro HTTPS Flood profiles via CyberController API.

- Fetches HTTPS Flood profiles from a DefensePro device.
- Maps API response values back to user-friendly keys.
- Returns structured response with raw, formatted, and summary data.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC

# Map API fields → user-friendly
REVERSE_FIELD_MAP = {
    "rsHttpsFloodProfileAction": "action",
    "rsHttpsFloodProfileRateLimitStatus": "rate_limit_status",
    "rsHttpsFloodProfileRateLimit": "rate_limit",
    "rsHttpsFloodProfileSelectiveChallenge": "http_authentication_on_suspect_sources",
    "rsHttpsFloodProfileCollectiveChallenge": "http_authentication_on_all_sources",
    "rsHttpsFloodProfileFullSessionDecryption": "full_session_decryption",
    "rsHttpsFloodProfileChallengeMethod": "challenge_method",
    "rsHttpsFloodProfilePacketReporting": "packet_report"
    
}

# Map numeric values → user-friendly
REVERSE_ENUM_MAPS = {
    "rsHttpsFloodProfileAction": {"0": "report_only", "1": "block_and_report"},
    "rsHttpsFloodProfileSelectiveChallenge": {"1": "enable", "2": "disable"},
    "rsHttpsFloodProfileCollectiveChallenge": {"1": "enable", "2": "disable"},
    "rsHttpsFloodProfileRateLimitStatus": {"1": "enable", "2": "disable"},
    "rsHttpsFloodProfileFullSessionDecryption": {"1": "enable", "2": "disable"},
    "rsHttpsFloodProfilePacketReporting": {"1": "enable", "2": "disable"},
    "rsHttpsFloodProfileChallengeMethod": {"1": "redirect_302", "2": "javascript"}

}


def format_http_profile_for_display(raw_profile):
    """
    Convert raw HTTPS Flood profile API data to user-friendly format
    """
    formatted_profile = {"profile_name": raw_profile.get("rsHttpsFloodProfileName", "unknown")}

    for api_field, user_field in REVERSE_FIELD_MAP.items():
        value = raw_profile.get(api_field)
        if value is not None:
            if api_field in REVERSE_ENUM_MAPS:
                formatted_profile[user_field] = REVERSE_ENUM_MAPS[api_field].get(str(value), value)
            else:
                formatted_profile[user_field] = value

    return formatted_profile


def run_module():
    module_args = dict(
        provider=dict(type="dict", required=True),
        dp_ip=dict(type="str", required=True),
        filter_profile_names=dict(type="list", required=False, default=[]),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    result = dict(changed=False, response={})
    debug_info = {}

    provider = module.params["provider"]
    dp_ip = module.params["dp_ip"]
    filter_profile_names = module.params["filter_profile_names"]

    log_level = provider.get("log_level", "disabled")
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(provider["cc_ip"], provider["username"], provider["password"], log_level=log_level, logger=logger)

    try:
        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsHttpsFloodProfileTable"
        logger.info(f"Fetching HTTPS Flood profiles from device {dp_ip}")
        resp = cc._get(url)
        data = resp.json()
        profiles_raw = data.get("rsHttpsFloodProfileTable", [])

        debug_info["profiles_raw_count"] = len(profiles_raw)

        # Apply filter if requested
        if filter_profile_names:
            profiles_raw = [p for p in profiles_raw if p.get("rsHttpsFloodProfileName") in filter_profile_names]
            logger.info(f"Filtered profiles to: {filter_profile_names}")

        formatted_profiles = [format_http_profile_for_display(p) for p in profiles_raw]
        profile_names = [p["profile_name"] for p in formatted_profiles]

        result["response"] = {
            "rsHttpsFloodProfileTable": profiles_raw,
            "formatted_profiles": formatted_profiles,
            "summary": {
                "total_entries": len(profiles_raw),
                "unique_profiles": len(profile_names),
                "profile_names": profile_names,
                "filtered": bool(filter_profile_names),
                "filter_applied": filter_profile_names if filter_profile_names else None,
            },
        }

        debug_info["summary"] = {
            "total_entries_retrieved": len(profiles_raw),
            "unique_profiles_found": len(profile_names),
            "filter_applied": bool(filter_profile_names),
            "profile_names_found": profile_names,
        }

        result["debug_info"] = debug_info
        module.exit_json(**result)

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        debug_info["error"] = str(e)
        module.fail_json(msg=str(e), debug_info=debug_info, **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
