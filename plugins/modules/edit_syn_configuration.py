"""
Unified Ansible module to edit DefensePro SYN protections, attach them to profiles,
and update SYN profile parameters.

Logging is aligned to match dp_lock formatting standards.
"""

from ansible.module_utils.basic import AnsibleModule

# Profile FIELD & VALUE mapping
FIELD_MAP = {
    "action": "rsIDSSynProfilesAction",
    "destination_ports": "rsIDSSynProfileDestinationPorts",
    "activation_mode": "rsIDSSynProfileActivationMode",
    "activation_threshold": "rsIDSSynProfileActivationThreshold",
    "termination_threshold": "rsIDSSynProfileTerminationThreshold",
    "auth_type": "rsIDSSynProfilesParamsAuthType",
    "tcp_reset_status": "rsIDSSynProfileTCPResetStatus",
}

VALUE_MAP = {
    "action": {"report_only": "0", "block_and_report": "1"},
    "activation_mode": {"continuous": "1", "threshold_based": "2"},
    "destination_ports": {"syn_profile": "1", "all": "2"},
    "auth_type": {"safe_reset": "1", "transparent_proxy": "2"},
    "tcp_reset_status": {"enable": "1", "disable": "2"},
}

REVERSE_VALUE_MAP = {
    key: {str(code): name for name, code in mapping.items()}
    for key, mapping in VALUE_MAP.items()
}
REVERSE_FIELD_MAP = {field: key for key, field in FIELD_MAP.items()}


def get_skip_reason(key, params):
    """Return why a visible DefensePro 10.10.1 control is not applicable."""
    if key == "tcp_reset_status":
        auth_type = str(params.get("auth_type") or "safe_reset").strip().lower()
        if auth_type != "safe_reset":
            return f"skipped (auth_type={auth_type})"

    return None


def map_syn_profile_parameters(profile_name, params, effective_params):
    """
    Build the rsIDSSynProfilesParamsTable body, dropping non-applicable parameters.
    ``effective_params`` merges the device state with the requested values so that
    unchanged settings still drive the applicability rules.
    """
    body = {"rsIDSSynProfilesParamsName": profile_name}
    applied = {}
    skipped = {}

    for key, value in params.items():
        field = FIELD_MAP.get(key)
        if not field:
            skipped[key] = "skipped (unknown parameter)"
            continue

        reason = get_skip_reason(key, effective_params)
        if reason:
            skipped[key] = reason
            continue

        body[field] = VALUE_MAP.get(key, {}).get(str(value).strip().lower(), str(value))
        applied[key] = value

    return body, applied, skipped


def fetch_current_params(cc, url_params, profile_name, logger):
    """
    Read the profile's current parameters row.
    Returns (current_user_friendly, raw_row): the user-friendly dict is used to drive
    dependency rules, and the raw API row (or None if the profile has no row yet) is
    used as the base for a full-row merge, since this table rejects partial writes.
    """
    try:
        resp = cc._get(url_params)
        payload = resp.json()
    except Exception as e:
        logger.debug(f"Could not read current params for '{profile_name}': {e}")
        return {}, None

    rows = payload.get("rsIDSSynProfilesParamsTable", payload)
    raw_row = None
    if isinstance(rows, list):
        raw_row = next(
            (r for r in rows if r.get("rsIDSSynProfilesParamsName") == profile_name),
            None,
        )
    elif isinstance(rows, dict):
        raw_row = rows

    if not isinstance(raw_row, dict):
        return {}, None

    current = {}
    for key, field in FIELD_MAP.items():
        value = raw_row.get(field)
        if value is None or str(value).strip() == "":
            continue
        current[key] = REVERSE_VALUE_MAP.get(key, {}).get(str(value).strip(), value)
    return current, raw_row


def merge_params_row(current_row, requested_params):
    """Apply requested values while retaining only controls exposed by DefensePro 10.10.1."""
    allowed_fields = set(REVERSE_FIELD_MAP) | {"rsIDSSynProfilesParamsName"}
    merged = {
        field: value
        for field, value in (current_row or {}).items()
        if field in allowed_fields
    }
    merged.update(requested_params)
    return merged


def applicable_subset(body, effective_params):
    """Drop columns that DefensePro's own GUI rules grey out for this combination.

    Columns not present in FIELD_MAP (e.g. the name key, or device-only columns like
    the per-policy termination threshold) are always kept since we have no rule for them.
    """
    subset = {}
    for field, value in body.items():
        key = REVERSE_FIELD_MAP.get(field)
        if key is None or get_skip_reason(key, effective_params) is None:
            subset[field] = value
    return subset


def known_fields_only(body):
    """Drop columns with no FIELD_MAP entry (e.g. rsIDSSynProfileTerminationThreshold) —
    these are device-schema columns we have no user-facing mapping or applicability rule
    for, and are likely read-only/derived from the attached protection, so echoing them
    back unmodified can still be rejected by the device."""
    return {
        field: value
        for field, value in body.items()
        if field == "rsIDSSynProfilesParamsName" or field in REVERSE_FIELD_MAP
    }


def write_params_row(cc, row_exists, url_params, full_body, effective_params, logger, attempts_out):
    """
    Write the parameter row with a cascade of fallback bodies and HTTP verbs.

    This table rejects some full-row writes with an opaque 500 (M_00386) that gives no
    field-level detail. A full-row body and a body limited to only the fields applicable
    to the final combined state can fail identically, which points at something common to
    both — namely the unmapped device-schema columns (e.g. termination threshold) that are
    always forwarded unmodified. So a known-fields-only body (mapped columns only) is also
    tried, and each body is retried with the opposite HTTP verb before giving up. Every
    attempt is appended to attempts_out for diagnosis regardless of outcome.
    """
    bodies = [("full_row", full_body)]
    applicable_body = applicable_subset(full_body, effective_params)
    if applicable_body != full_body:
        bodies.append(("applicable_fields_only", applicable_body))

    known_body = known_fields_only(applicable_body)
    if known_body != applicable_body:
        bodies.append(("known_fields_only", known_body))

    primary_verb, secondary_verb = ("put", "post") if row_exists else ("post", "put")
    verb_fn = {"put": cc._put, "post": cc._post}

    last_exc = None
    for label, body in bodies:
        for verb in (primary_verb, secondary_verb):
            strategy = f"{label}_{verb}"
            try:
                resp = verb_fn[verb](url_params, json=body)
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw_text": resp.text}
                attempts_out.append({"strategy": strategy, "body": body, "status": "success"})
                return data, strategy
            except Exception as exc:
                attempts_out.append({"strategy": strategy, "body": body, "status": "failed", "error": str(exc)})
                last_exc = exc
                logger.debug(f"Write strategy '{strategy}' failed: {exc}")

    raise last_exc


def run_module():
    module_args = dict(
        provider=dict(type="dict", required=True),
        dp_ip=dict(type="str", required=True),
        syn_protections=dict(type="list", required=False, default=[]),
        syn_profiles=dict(type="list", required=False, default=[]),
    )

    result = dict(changed=False, response={})
    debug_info = {"operations": []}

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params["provider"]
    dp_ip = module.params["dp_ip"]
    syn_protections = module.params["syn_protections"]
    syn_profiles = module.params["syn_profiles"]
    check_mode = module.check_mode

    # ------------------ LOGGER SETUP ------------------
    log_level = provider.get("log_level", "disabled")
    from ansible.module_utils.logger import Logger

    logger = Logger(verbosity=log_level)
    from ansible.module_utils.radware_cc import RadwareCC

    logger.info("======================================================")
    logger.info("Starting SYN configuration update process")
    logger.info(f"Target CC: {provider.get('cc_ip')} | DP: {dp_ip}")
    logger.info("======================================================")

    cc = RadwareCC(provider["cc_ip"], provider["username"], provider["password"], 
                   log_level=log_level, logger=logger)

    logger.info("Connected to Radware CC successfully")

    logger.debug(
        f"Input received: dp_ip={dp_ip}, protections={len(syn_protections)}, profiles={len(syn_profiles)}"
    )
    debug_info["input"] = {
        "dp_ip": dp_ip,
        "protections_count": len(syn_protections),
        "profiles_count": len(syn_profiles),
    }

    try:
        changes_made = False
        edited_protections = []
        edited_profiles = []


        if syn_protections:
            logger.info("======================================================")
            logger.info("[STEP] Editing SYN Protections")
            logger.info("======================================================")

        # Resolve IDs by name so a stale id in the vars file does not target the wrong row
        protection_ids = {}
        if syn_protections:
            try:
                prot_table_url = (
                    f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable"
                )
                for row in cc._get(prot_table_url).json().get("rsIDSSYNAttackTable", []):
                    name = row.get("rsIDSSYNAttackName")
                    if name:
                        protection_ids[name] = row.get("rsIDSSYNAttackId")
                logger.debug(f"Resolved {len(protection_ids)} SYN protections on {dp_ip}")
            except Exception as e:
                logger.debug(f"Could not list SYN protections (falling back to supplied ids): {e}")

        for protection in syn_protections:
            prot_name = protection.get("name")
            prot_id = protection_ids.get(prot_name) or protection.get("id")
            if not prot_id:
                logger.error(f"Skipping SYN protection '{prot_name}': no id found on device")
                continue

            url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/{prot_id}"

            # The device requires the name (its key, max 29 chars) on every protection write
            body = {
                key: value
                for key, value in {
                    "rsIDSSYNAttackName": prot_name,
                    "rsIDSSYNAttackActivationThreshold": protection.get("activation_threshold"),
                    "rsIDSSYNAttackTerminationThreshold": protection.get("termination_threshold"),
                    "rsIDSSYNDestinationAppPortGroup": protection.get("app_port_group"),
                }.items()
                if value is not None
            }

            logger.info(f"Editing SYN protection '{prot_name}' (ID {prot_id})")

            logger.debug(f"Request: {{'method': 'PUT', 'url': '{url}', 'body': {body}}}")

            # Recorded before the request so a failed PUT still reports the body
            protection_operation = {
                "type": "protection_edit",
                "id": prot_id,
                "name": prot_name,
                "uri": url,
                "body": body,
                "response": None,
            }
            debug_info["operations"].append(protection_operation)

            if not check_mode:
                resp = cc._put(url, json=body)

                logger.debug(f"Response status: {resp.status_code}")

                try:
                    data = resp.json()
                except Exception:
                    data = {"status": "ok"}

                logger.debug(f"Response JSON: {data}")
            else:
                data = {"status": "check_mode_skipped"}

            protection_operation["response"] = data

            edited_protections.append(
                {
                    "id": prot_id,
                    "name": prot_name,
                    "parameters": {
                        "activation_threshold": protection.get("activation_threshold"),
                        "termination_threshold": protection.get("termination_threshold"),
                        "app_port_group": protection.get("app_port_group"),
                    },
                    "body": body,
                    "response": data,
                }
            )
            changes_made = True

        attached_map = {}

        if syn_profiles:
            logger.info("======================================================")
            logger.info("[STEP] Attaching Protections to Profiles")
            logger.info("======================================================")

        for profile in syn_profiles:
            profile_name = profile.get("name")
            protections = profile.get("protections", [])
            if not profile_name or not protections:
                continue

            for protection_name in protections:
                url_attach = (
                    f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}"
                    f"/config/rsIDSSynProfilesTable/{profile_name}/{protection_name}"
                )

                body_attach = {
                    "rsIDSSynProfilesName": profile_name,
                    "rsIDSSynProfileServiceName": protection_name,
                }

                logger.info(f"Attaching '{protection_name}' → Profile '{profile_name}'")
                logger.debug(f"Request: {{'method': 'POST', 'url': '{url_attach}', 'body': {body_attach}}}")

                if not check_mode:
                    try:
                        cc._post(url_attach, json=body_attach)
                    except Exception as e:
                        if "already exists" in str(e) or "M_00386" in str(e):
                            logger.debug("Attachment exists — retrying with PUT")
                            cc._put(url_attach, json=body_attach)
                        else:
                            raise

                attached_map.setdefault(profile_name, []).append(protection_name)

                debug_info["operations"].append(
                    {
                        "type": "profile_attach",
                        "profile": profile_name,
                        "protection": protection_name,
                        "uri": url_attach,
                        "body": body_attach,
                    }
                )
                changes_made = True


        if syn_profiles:
            logger.info("======================================================")
            logger.info("[STEP] Updating Profile Parameters")
            logger.info("======================================================")

        for profile in syn_profiles:
            profile_name = profile.get("name")
            params = profile.get("params", {})
            if not params:
                continue

            logger.info(f"Updating parameters for profile '{profile_name}'")

            url_params = (
                f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/"
                f"rsIDSSynProfilesParamsTable/{profile_name}"
            )

            # Merge with the device state so unchanged values still drive the dependency rules
            current_params, current_row = fetch_current_params(cc, url_params, profile_name, logger)
            effective_params = dict(current_params)
            effective_params.update(params)

            body_params, applied_params, skip_fields = map_syn_profile_parameters(
                profile_name, params, effective_params
            )

            for key, reason in skip_fields.items():
                logger.debug(f"Profile '{profile_name}': {reason} for parameter '{key}'")

            # This table rejects partial-column writes with an opaque 500 error, so the full
            # current row must be read, merged with the requested changes, and written back whole.
            request_body = merge_params_row(current_row, body_params)
            params_changed = current_row is None or any(
                str(current_row.get(field)) != str(value)
                for field, value in body_params.items()
            )
            method = ("PUT" if current_row else "POST") if params_changed else "SKIP"

            logger.debug(f"Request: {{'method': '{method}', 'url': '{url_params}', 'body': {request_body}}}")

            # Recorded before the request so a failed write still reports the body
            params_operation = {
                "type": "profile_edit",
                "name": profile_name,
                "uri": url_params,
                "method": method,
                "body": request_body,
                "skipped": skip_fields,
                "response": None,
            }
            debug_info["operations"].append(params_operation)

            if check_mode:
                data = {"status": "check_mode_skipped"}
            elif not params_changed:
                data = {"status": "already_configured"}
            else:
                write_attempts = []
                data, strategy_used = write_params_row(
                    cc, bool(current_row), url_params, request_body,
                    effective_params, logger, write_attempts
                )
                params_operation["write_strategy"] = strategy_used
                params_operation["write_attempts"] = write_attempts
                if strategy_used != "full_row":
                    logger.info(
                        f"Profile '{profile_name}': full-row write rejected by device; "
                        f"succeeded using '{strategy_used}' fallback"
                    )

                logger.debug(f"Response JSON: {data}")

            params_operation["response"] = data

            edited_profiles.append(
                {
                    "profile_name": profile_name,
                    "protection_names": attached_map.get(profile_name, []),
                    "parameters": applied_params,
                    "applied_body": request_body,
                    "skipped": skip_fields,
                    "response": data,
                }
            )
            if not check_mode and params_changed:
                changes_made = True

        logger.info("======================================================")
        logger.info("SYN configuration completed successfully")
        logger.info("======================================================")

        result["changed"] = changes_made
        result["response"] = {
            "protections": edited_protections,
            "profiles": edited_profiles,
            "summary": {
                "total_protections_attempted": len(syn_protections),
                "protections_edited": len(edited_protections),
                "total_profiles_attempted": len(syn_profiles),
                "profiles_updated": len(edited_profiles),
            },
        }
        result["debug_info"] = debug_info

        module.exit_json(**result)

    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        result["debug_info"] = debug_info
        module.fail_json(msg=str(e), **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
