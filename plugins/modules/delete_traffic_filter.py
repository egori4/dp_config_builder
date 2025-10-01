"""
Unified Ansible module to delete DefensePro Traffic Filter profiles and protections.
Aligned with edit_traffic_filter for consistent logging, debug info, and summary reporting.
"""

from ansible.module_utils.basic import AnsibleModule


def pretty_deleted_protections(protections):
    """Return nicely formatted string of deleted protections."""
    lines = []
    for prot in protections:
        profile_name = prot.get("profile_name")
        protection_name = prot.get("protection_name")
        status = "deleted" if prot.get("status") == "success" else f"failed: {prot.get('error', 'unknown error')}"
        lines.append(f"  - {protection_name} (Profile: {profile_name}) -> {status}")
    return "\n".join(lines)


def pretty_deleted_profiles(profiles):
    """Return nicely formatted string of deleted profiles."""
    lines = []
    for prof in profiles:
        profile_name = prof.get("profile_name")
        status = "deleted" if prof.get("status") == "success" else f"failed: {prof.get('error', 'unknown error')}"
        lines.append(f"  - {profile_name} -> {status}")
    return "\n".join(lines)


def run_module():
    module_args = dict(
        provider=dict(type="dict", required=True),
        dp_ip=dict(type="str", required=True),
        traffic_filters=dict(type="dict", required=False, default={}),
    )

    result = dict(changed=False, response={}, debug_info={}, errors=[])
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

        deleted_profiles = []
        deleted_protections = []
        changes_made = False
        errors = []

        if module.check_mode:
            preview_ops = {"profiles": profiles, "protections": protections}
            result.update(
                {
                    "changed": bool(profiles or protections),
                    "response": {
                        "preview_mode": True,
                        "planned_operations": preview_ops,
                    },
                }
            )
            module.exit_json(**result)

        # === Delete protections first ===
        for prot in protections:
            profile_name = prot.get("profile_name")
            protection_name = prot.get("protection_name") or prot.get("name")
            if not profile_name or not protection_name:
                err = "Protection requires 'profile_name' and 'protection_name'"
                errors.append(err)
                logger.error(err)
                deleted_protections.append(
                    {"profile_name": profile_name, "protection_name": protection_name, "status": "failed", "error": err}
                )
                continue
            try:
                url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficFilterTable/{profile_name}/{protection_name}"
                logger.info(f"Deleting Traffic Filter protection '{protection_name}' under profile '{profile_name}'")
                resp = cc._delete(url)
                data = resp.json() if hasattr(resp, "json") else {"status": resp.status_code}
                logger.debug(f"Delete protection response: {data}")
                deleted_protections.append(
                    {"profile_name": profile_name, "protection_name": protection_name, "status": "success", "response": data}
                )
                changes_made = True
            except Exception as e:
                err_msg = f"Failed to delete protection {protection_name} under profile {profile_name}: {str(e)}"
                logger.error(err_msg)
                deleted_protections.append(
                    {"profile_name": profile_name, "protection_name": protection_name, "status": "failed", "error": err_msg}
                )
                errors.append(err_msg)

        # === Delete profiles ===
        for profile in profiles:
            profile_name = profile.get("profile_name") or profile.get("name")
            if not profile_name:
                err = "Profile requires 'profile_name'"
                errors.append(err)
                logger.error(err)
                deleted_profiles.append({"profile_name": profile_name, "status": "failed", "error": err})
                continue
            try:
                url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsNewTrafficProfileTable/{profile_name}"
                logger.info(f"Deleting Traffic Filter profile '{profile_name}'")
                resp = cc._delete(url)
                data = resp.json() if hasattr(resp, "json") else {"status": resp.status_code}
                logger.debug(f"Delete profile response: {data}")
                deleted_profiles.append({"profile_name": profile_name, "status": "success", "response": data})
                changes_made = True
            except Exception as e:
                err_msg = f"Failed to delete profile {profile_name}: {str(e)}"
                logger.error(err_msg)
                deleted_profiles.append({"profile_name": profile_name, "status": "failed", "error": err_msg})
                errors.append(err_msg)

        # Final result
        result.update(
            {
                "changed": changes_made,
                "response": {
                    "deleted_profiles": deleted_profiles,
                    "deleted_protections": deleted_protections,
                    "pretty_profiles": pretty_deleted_profiles(deleted_profiles),
                    "pretty_protections": pretty_deleted_protections(deleted_protections),
                    "summary": {
                        "successful_profiles": len([p for p in deleted_profiles if p["status"] == "success"]),
                        "successful_protections": len([p for p in deleted_protections if p["status"] == "success"]),
                        "total_profiles_attempted": len(profiles),
                        "total_protections_attempted": len(protections),
                        "errors_count": len(errors),
                    },
                },
                "debug_info": debug_info,
                "errors": errors,
            }
        )

    except Exception as e:
        module.fail_json(msg=f"Traffic Filter delete failed: {str(e)}", debug_info=debug_info, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
