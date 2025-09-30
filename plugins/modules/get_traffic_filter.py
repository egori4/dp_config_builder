"""
Ansible module to fetch DefensePro Traffic Filter profiles and associated protections.

- Fetches profiles and protections from a DefensePro device via CyberController API.
- Returns only relevant information: profile -> protections mapping + summary.
- Logs main actions with logger.info and raw API responses with logger.debug.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC

# Mapping API values to user-friendly strings
ENABLED_DISABLED_MAP = {"1": "enabled", "2": "disabled"}
PROTOCOL_MAP = {
    "0": "any", "1": "tcp", "2": "udp", "3": "icmp", "4": "igmp",
    "5": "sctp", "6": "icmpv6", "7": "gre", "8": "ipinip"
}
ACTION_MAP = {"0": "report_only", "1": "report_only", "10": "drop"}


def run_module():
    module_args = dict(
        provider=dict(type="dict", required=True),
        dp_ip=dict(type="str", required=True),
        filter_tf_profile_names=dict(type="list", required=False, default=[]),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params["provider"]
    dp_ip = module.params["dp_ip"]
    filter_tf_profile_names = module.params["filter_tf_profile_names"]

    log_level = provider.get("log_level", "disabled")
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(
        provider["cc_ip"], provider["username"], provider["password"],
        log_level=log_level, logger=logger
    )

    try:
        # Fetch all traffic filter profiles
        profile_url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficProfileTable"
        logger.info(f"Fetching Traffic Filter profiles from {dp_ip}")
        resp_profiles = cc._get(profile_url)
        profiles_raw = resp_profiles.json().get("rsNewTrafficProfileTable", [])
        logger.debug(f"Raw profiles data: {profiles_raw}")

        # Fetch all protections
        prot_url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficFilterTable"
        logger.info(f"Fetching Traffic Filter protections from {dp_ip}")
        resp_prots = cc._get(prot_url)
        protections_raw = resp_prots.json().get("rsNewTrafficFilterTable", [])
        logger.debug(f"Raw protections data: {protections_raw}")

        # Build nested profile structure
        profiles = {}
        for prof in profiles_raw:
            prof_name = prof.get("rsNewTrafficProfileName")
            if prof_name not in profiles:
                profiles[prof_name] = {
                    "profile_name": prof_name,
                    "num_of_rules": int(prof.get("rsNewTrafficProfileNumOfRules", 0)),
                    "action": ACTION_MAP.get(prof.get("rsNewTrafficProfileAction", ""), prof.get("rsNewTrafficProfileAction", "")),
                    "protections": []
                }

        # Add protections to profiles
        for prot in protections_raw:
            prof_name = prot.get("rsNewTrafficFilterProfileName")
            if prof_name in profiles:
                prot_entry = {
                    "protection_name": prot.get("rsNewTrafficFilterName"),
                    "protection_id": prot.get("rsNewTrafficFilterID"),
                    "state": ENABLED_DISABLED_MAP.get(prot.get("rsNewTrafficFilterState", ""), prot.get("rsNewTrafficFilterState", "")),
                    "priority": prot.get("rsNewTrafficFilterPriority", "0"),
                    "protocol": PROTOCOL_MAP.get(prot.get("rsNewTrafficFilterProtocol", ""), prot.get("rsNewTrafficFilterProtocol", "")),
                    "threshold_pps": prot.get("rsNewTrafficFilterThresholdPPS", "0"),
                    "threshold_bps": prot.get("rsNewTrafficFilterThresholdBPS", "0"),
                    "packet_report": ENABLED_DISABLED_MAP.get(prot.get("rsNewTrafficFilterPacketReport", ""), prot.get("rsNewTrafficFilterPacketReport", "")),
                    "vlan": prot.get("rsNewTrafficFilterVLAN", "Any"),
                    "src_network": prot.get("rsNewTrafficFilterSrcNetwork", ""),
                    "src_port": prot.get("rsNewTrafficFilterSrcPort", ""),
                    "dst_network": prot.get("rsNewTrafficFilterDstNetwork", ""),
                    "dst_port": prot.get("rsNewTrafficFilterDstPort", ""),
                    # TCP flags
                    "tcp_syn": ENABLED_DISABLED_MAP.get(prot.get("rsNewTrafficFilterTCPFlagsSyn", ""), prot.get("rsNewTrafficFilterTCPFlagsSyn", "")),
                    "tcp_ack": ENABLED_DISABLED_MAP.get(prot.get("rsNewTrafficFilterTCPFlagsAck", ""), prot.get("rsNewTrafficFilterTCPFlagsAck", "")),
                    "tcp_rst": ENABLED_DISABLED_MAP.get(prot.get("rsNewTrafficFilterTCPFlagsRst", ""), prot.get("rsNewTrafficFilterTCPFlagsRst", "")),
                    "tcp_synack": ENABLED_DISABLED_MAP.get(prot.get("rsNewTrafficFilterTCPFlagsSynAck", ""), prot.get("rsNewTrafficFilterTCPFlagsSynAck", "")),
                    "tcp_finack": ENABLED_DISABLED_MAP.get(prot.get("rsNewTrafficFilterTCPFlagsFinAck", ""), prot.get("rsNewTrafficFilterTCPFlagsFinAck", "")),
                    "tcp_pshack": ENABLED_DISABLED_MAP.get(prot.get("rsNewTrafficFilterTCPFlagsPshAck", ""), prot.get("rsNewTrafficFilterTCPFlagsPshAck", ""))
                }
                profiles[prof_name]["protections"].append(prot_entry)

        # Apply profile filter if provided
        all_profiles = list(profiles.values())
        if filter_tf_profile_names:
            filtered_profiles = [p for p in all_profiles if p["profile_name"] in filter_tf_profile_names]
            profiles_to_return = filtered_profiles
            logger.info(f"Filtered profiles to: {filter_tf_profile_names}")
        else:
            profiles_to_return = all_profiles

        # Build summary
        summary = {
            "total_profiles": len(profiles_to_return),
            "total_protections": sum(len(p["protections"]) for p in profiles_to_return)
        }

        # Return only relevant info
        module.exit_json(profiles=profiles_to_return, summary=summary)

    except Exception as e:
        logger.error(f"Exception fetching Traffic Filter data: {str(e)}")
        module.fail_json(msg=str(e))


def main():
    run_module()


if __name__ == "__main__":
    main()
