"""
Ansible module to fetch DefensePro Traffic Filter profiles and associated protections.
"""

from ansible.module_utils.basic import AnsibleModule

ENABLED_DISABLED_MAP = {"1": "enable", "2": "disable"}
PROTOCOL_MAP = {
    "0": "any", "1": "tcp", "2": "udp", "3": "icmp", "4": "igmp",
    "5": "sctp", "6": "icmpv6", "7": "gre", "8": "ipinip"
}
ACTION_MAP = {"0": "report_only", "1": "block_and_report"}
THRESHOLD_USED_MAP = {"2": "pps", "1": "kbps"}

def run_module():
    module_args = dict(
        provider=dict(type="dict", required=True),
        dp_ip=dict(type="str", required=True),
        filter_tf_profile_names=dict(type="list", required=False, default=[]),
    )

    result = dict(changed=False, profiles=[], summary={}, debug_info={}, errors=[])
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params["provider"]
    dp_ip = module.params["dp_ip"]
    filter_tf_profile_names = module.params["filter_tf_profile_names"]

    try:
        from ansible.module_utils.radware_cc import RadwareCC
        from ansible.module_utils.logger import Logger
    except ImportError:
        module.fail_json(msg="Missing module utilities: radware_cc or logger.")

    log_level = provider.get("log_level", "disabled")
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(
        provider["cc_ip"], provider["username"], provider["password"],
        log_level=log_level, logger=logger
    )

    debug_info = {}

    try:
        # === Fetch Traffic Filter profiles ===
        profile_url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficProfileTable"
        logger.info(f"Fetching Traffic Filter profiles from {dp_ip}")
        resp_profiles = cc._get(profile_url)

        debug_info['profiles_request'] = {
            "method": "GET",
            "url": profile_url,
            "status_code": resp_profiles.status_code,
            "response_json": resp_profiles.json() if hasattr(resp_profiles, 'json') else None
        }

        try:
            profiles_raw = resp_profiles.json().get("rsNewTrafficProfileTable", [])
        except Exception:
            profiles_raw = []
            result['errors'].append(f"Failed to parse profiles JSON from {dp_ip}")
            logger.error(f"Failed to parse profiles JSON from {dp_ip}")

        logger.debug(f"Fetched {len(profiles_raw)} Traffic Filter profiles from {dp_ip}")

        # === Fetch Traffic Filter protections ===
        prot_url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficFilterTable"
        logger.info(f"Fetching Traffic Filter protections from {dp_ip}")
        resp_prots = cc._get(prot_url)

        debug_info['protections_request'] = {
            "method": "GET",
            "url": prot_url,
            "status_code": resp_prots.status_code,
            "response_json": resp_prots.json() if hasattr(resp_prots, 'json') else None
        }

        try:
            protections_raw = resp_prots.json().get("rsNewTrafficFilterTable", [])
        except Exception:
            protections_raw = []
            result['errors'].append(f"Failed to parse protections JSON from {dp_ip}")
            logger.error(f"Failed to parse protections JSON from {dp_ip}")

        logger.debug(f"Fetched {len(protections_raw)} Traffic Filter protections from {dp_ip}")

        # === Build profiles dictionary ===
        profiles = {}
        for prof in profiles_raw:
            prof_name = prof.get("rsNewTrafficProfileName")
            if not prof_name:
                continue
            if prof_name not in profiles:
                profiles[prof_name] = {
                    "profile_name": prof_name,
                    "num_of_rules": int(prof.get("rsNewTrafficProfileNumOfRules", 0)),
                    "action": ACTION_MAP.get(prof.get("rsNewTrafficProfileAction", ""), prof.get("rsNewTrafficProfileAction", "")),
                    "protections": []
                }

        # === Add protections to profiles ===
        for prot in protections_raw:
            prof_name = prot.get("rsNewTrafficFilterProfileName")
            if prof_name in profiles:
                prot_entry = {
                    "protection_name": prot.get("rsNewTrafficFilterName"),
                    "protection_id": prot.get("rsNewTrafficFilterID"),
                    "state": ENABLED_DISABLED_MAP.get(prot.get("rsNewTrafficFilterState", ""), prot.get("rsNewTrafficFilterState", "")),
                    "protocol": PROTOCOL_MAP.get(prot.get("rsNewTrafficFilterProtocol", ""), prot.get("rsNewTrafficFilterProtocol", "")),
                    "threshold_pps": prot.get("rsNewTrafficFilterThresholdPPS", "0"),
                    "threshold_kbps": prot.get("rsNewTrafficFilterThresholdBPS", "0"),
                    "threshold_unit": THRESHOLD_USED_MAP.get(prot.get("rsNewTrafficFilterThresholdUsed", "0"), prot.get("rsNewTrafficFilterThresholdUsed", "")),
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
                    "tcp_pshack": ENABLED_DISABLED_MAP.get(prot.get("rsNewTrafficFilterTCPFlagsPshAck", ""), prot.get("rsNewTrafficFilterTCPFlagsPshAck", "")),
                }
                profiles[prof_name]["protections"].append(prot_entry)

        # === Apply filter if requested ===
        all_profiles = list(profiles.values())
        if filter_tf_profile_names:
            profiles_to_return = [p for p in all_profiles if p["profile_name"] in filter_tf_profile_names]
            logger.info(f"Filtered profiles to: {filter_tf_profile_names}")
        else:
            profiles_to_return = all_profiles

        # === Build summary ===
        summary = {
            "total_profiles": len(profiles_to_return),
            "total_protections": sum(len(p["protections"]) for p in profiles_to_return),
        }

        result.update(
            profiles=profiles_to_return,
            summary=summary,
            debug_info=debug_info
        )

        logger.debug(f"Traffic Filter fetch summary for {dp_ip}: {summary}")

    except Exception as e:
        logger.error(f"Exception fetching Traffic Filter data: {str(e)}")
        result['errors'].append(str(e))
        module.fail_json(msg=f"Traffic Filter fetch failed: {str(e)}", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
