"""
Unified Ansible module to delete DefensePro Traffic Filter profiles and protections.
Handles failures gracefully and reports deleted items.
"""

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type="dict", required=True),
        dp_ip=dict(type="str", required=True),
        traffic_filters=dict(type="dict", required=False, default={})
    )

    result = dict(changed=False, response={}, failed_items=[], debug_info={})
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

        if not module.check_mode:
            # === Delete protections first ===
            for prot in protections:
                profile_name = prot["profile_name"]
                protection_name = prot["name"]
                try:
                    path = f"/mgmt/device/byip/{dp_ip}/config/rsNewTrafficFilterTable/{profile_name}/{protection_name}"
                    url = f"https://{provider['cc_ip']}{path}"
                    logger.info(f"Deleting Traffic Filter protection '{protection_name}' under profile '{profile_name}'")
                    resp = cc._delete(url)
                    data = resp.json() if hasattr(resp, "json") else {"status": resp.status_code}
                    deleted_protections.append({
                        "profile_name": profile_name,
                        "protection_name": protection_name,
                        "response": data
                    })
                    result["changed"] = True
                except Exception as e:
                    deleted_protections.append({
                        "profile_name": profile_name,
                        "protection_name": protection_name,
                        "error": str(e)
                    })
                    result["failed_items"].append(f"{profile_name}/{protection_name}: {str(e)}")

            # === Delete profiles ===
            for profile in profiles:
                profile_name = profile["name"]
                try:
                    path = f"/mgmt/device/byip/{dp_ip}/config/rsNewTrafficProfileTable/{profile_name}"
                    url = f"https://{provider['cc_ip']}{path}"
                    logger.info(f"Deleting Traffic Filter profile '{profile_name}'")
                    resp = cc._delete(url)
                    data = resp.json() if hasattr(resp, "json") else {"status": resp.status_code}
                    deleted_profiles.append({
                        "profile_name": profile_name,
                        "response": data
                    })
                    result["changed"] = True
                except Exception as e:
                    deleted_profiles.append({
                        "profile_name": profile_name,
                        "error": str(e)
                    })
                    result["failed_items"].append(f"{profile_name}: {str(e)}")

        result["response"] = {
            "deleted_profiles": deleted_profiles,
            "deleted_protections": deleted_protections,
        }
        result["debug_info"] = debug_info

    except Exception as e:
        module.fail_json(msg=f"Module execution failed: {str(e)}", debug_info=debug_info)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
