# plugins/modules/get_dns_profile.py
"""
Ansible module to fetch DefensePro DNS Protection profiles via CyberController API.

- Fetches DNS profiles from a DefensePro device.
- Maps API response values back to user-friendly keys.
- Returns structured response with raw, formatted, and summary data.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC


# Reverse mapping for API fields → user-friendly
REVERSE_FIELD_MAP = {
    "rsDnsProtProfileAction": "action",
    "rsDnsProtProfilePacketReportStatus": "packet_report",
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
    "rsDnsProtProfileDnsAStatus": "a_status",
    "rsDnsProtProfileDnsMxStatus": "mx_status",
    "rsDnsProtProfileDnsPtrStatus": "ptr_status",
    "rsDnsProtProfileDnsAaaaStatus": "aaaa_status",
    "rsDnsProtProfileDnsTextStatus": "text_status",
    "rsDnsProtProfileDnsSoaStatus": "soa_status",
    "rsDnsProtProfileDnsNaptrStatus": "naptr_status",
    "rsDnsProtProfileDnsSrvStatus": "srv_status",
    "rsDnsProtProfileDnsOtherStatus": "other_status",
    "rsDnsProtProfileFootprintStrictness": "footprint_strictness",
    "rsDnsProtProfileLearningSuppressionThreshold": "learning_suppression_threshold",
    "rsDnsProtProfileManualTriggerStatus": "manual_trigger"

}
REVERSE_ENUM_MAPS = {
    "rsDnsProtProfileAction": {"0": "report_only", "1": "block_&_report"},
    "rsDnsProtProfileManualTriggerStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfilePacketReportStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfilePacketTraceStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileFootprintStrictness": {"0": "low", "1": "medium", "2": "high"},
    "rsDnsProtProfileDnsAStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsMxStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsPtrStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsAaaaStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsTextStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsSoaStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsNaptrStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsSrvStatus": {"1": "enable", "2": "disable"},
    "rsDnsProtProfileDnsOtherStatus": {"1": "enable", "2": "disable"},
}


def format_dns_profile_for_display(raw_profile):
    """
    Convert raw DNS profile API data to user-friendly format
    """
    formatted = {"profile_name": raw_profile.get("rsDnsProtProfileName", "unknown")}
    for api_field, user_field in REVERSE_FIELD_MAP.items():
        value = raw_profile.get(api_field)
        if value is not None:
            if api_field in REVERSE_ENUM_MAPS:
                formatted[user_field] = REVERSE_ENUM_MAPS[api_field].get(str(value), value)
            else:
                formatted[user_field] = value
    return formatted


def run_module():
    module_args = dict(
        provider=dict(type="dict", required=True),
        dp_ip=dict(type="str", required=True),
        filter_dns_profile_names=dict(type="list", required=False, default=[]),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    result = dict(changed=False, response={})
    debug_info = {}

    provider = module.params["provider"]
    dp_ip = module.params["dp_ip"]
    filter_dns_profile_names = module.params["filter_dns_profile_names"]

    log_level = provider.get("log_level", "disabled")
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(provider["cc_ip"], provider["username"], provider["password"], log_level=log_level, logger=logger)

    try:
        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable"
        logger.info(f"Fetching DNS profiles from device {dp_ip}")
        resp = cc._get(url)
        data = resp.json()
        profiles_raw = data.get("rsDnsProtProfileTable", [])

        debug_info["profiles_raw_count"] = len(profiles_raw)

        # Apply filter
        if filter_dns_profile_names:
            profiles_raw = [p for p in profiles_raw if p.get("rsDnsProtProfileName") in filter_dns_profile_names]
            logger.info(f"Filtered profiles to: {filter_dns_profile_names}")

        formatted_profiles = [format_dns_profile_for_display(p) for p in profiles_raw]
        profile_names = [p["profile_name"] for p in formatted_profiles]

        result["response"] = {
            "rsDnsProtProfileTable": profiles_raw,
            "formatted_profiles": formatted_profiles,
            "summary": {
                "total_entries": len(profiles_raw),
                "unique_profiles": len(profile_names),
                "profile_names": profile_names,
                "filtered": bool(filter_dns_profile_names),
                "filter_applied": filter_dns_profile_names if filter_dns_profile_names else None,
            },
        }

        debug_info["summary"] = {
            "total_entries_retrieved": len(profiles_raw),
            "unique_profiles_found": len(profile_names),
            "filter_applied": bool(filter_dns_profile_names),
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
