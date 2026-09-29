"""
Unified Ansible module to create DefensePro SYN protections and profiles.

Errors are collected per object so one failure does not hide the rest of the run.
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

PARAMS_NAME_FIELD = "rsIDSSynProfilesParamsName"

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


def map_syn_profile_parameters(profile_name, params):
    """Build the rsIDSSynProfilesParamsTable body, dropping non-applicable parameters."""
    body = {PARAMS_NAME_FIELD: profile_name}
    applied = {}
    skipped = {}

    for key, value in params.items():
        field = FIELD_MAP.get(key)
        if not field:
            skipped[key] = "skipped (unknown parameter)"
            continue

        reason = get_skip_reason(key, params)
        if reason:
            skipped[key] = reason
            continue

        body[field] = VALUE_MAP.get(key, {}).get(str(value).strip().lower(), str(value))
        applied[key] = value

    return body, applied, skipped


def merge_params_row(current_row, requested_params):
    """Apply requested values while retaining only controls exposed by DefensePro 10.10.1."""
    allowed_fields = set(REVERSE_FIELD_MAP) | {PARAMS_NAME_FIELD}
    merged = {
        field: value
        for field, value in (current_row or {}).items()
        if field in allowed_fields
    }
    merged.update(requested_params)
    return merged


def row_to_user_params(row):
    """Reverse-map a raw rsIDSSynProfilesParamsTable row to user-friendly keys/values."""
    result = {}
    for key, field in FIELD_MAP.items():
        value = row.get(field)
        if value is None or str(value).strip() == "":
            continue
        result[key] = REVERSE_VALUE_MAP.get(key, {}).get(str(value).strip(), value)
    return result


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
        if field == PARAMS_NAME_FIELD or field in REVERSE_FIELD_MAP
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
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        syn_protections=dict(type='list', required=False, default=[]),
        syn_profiles=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={})
    debug_info = {"operations": []}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    syn_protections = module.params['syn_protections']
    syn_profiles = module.params['syn_profiles']

    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    logger.debug(f"Module input: dp_ip={dp_ip}, protections_count={len(syn_protections)}, profiles_count={len(syn_profiles)}")
    debug_info['input'] = {'dp_ip': dp_ip, 'protections_count': len(syn_protections), 'profiles_count': len(syn_profiles)}

    if module.check_mode:
        result.update({
            'changed': bool(syn_protections or syn_profiles),
            'response': {
                'preview_mode': True,
                'planned_protections': [p.get('name', 'unnamed_protection') for p in syn_protections],
                'planned_profiles': [
                    {
                        'profile_name': p.get('name', 'unnamed_profile'),
                        'protections': p.get('protections', []),
                        'params': p.get('params', {})
                    } for p in syn_profiles
                ]
            },
            'debug_info': debug_info
        })
        module.exit_json(**result)

    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'],
                       provider['password'], log_level=log_level, logger=logger)

        changes_made = False
        created_protections = []
        created_profiles = []
        errors = []

        protection_rows = get_table_rows(cc, provider, dp_ip, "rsIDSSYNAttackTable")
        existing_protections = {
            row.get("rsIDSSYNAttackName"): row for row in protection_rows
            if row.get("rsIDSSYNAttackName")
        }
        profile_rows = get_table_rows(cc, provider, dp_ip, "rsIDSSynProfilesTable")
        existing_attachments = {
            (row.get("rsIDSSynProfilesName"), row.get("rsIDSSynProfileServiceName"))
            for row in profile_rows
        }

        # ---------------- SYN Protections ----------------
        for protection in syn_protections:
            protection_name = protection.get('name', 'unnamed_protection')
            body = {
                "rsIDSSYNAttackName": protection_name,
                "rsIDSSYNAttackActivationThreshold": protection.get("activation_threshold", 1000),
                "rsIDSSYNAttackTerminationThreshold": protection.get("termination_threshold", 500),
                "rsIDSSYNDestinationAppPortGroup": protection.get("app_port_group", "")
            }
            url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/0"

            operation = {
                "type": "protection_create",
                "name": protection_name,
                "method": "POST",
                "uri": url,
                "request_body": body,
                "response": None
            }
            debug_info['operations'].append(operation)

            if protection_name in existing_protections:
                operation["method"] = "SKIP"
                operation["response"] = {"status": "already_exists"}
                status = "already_exists"
            else:
                try:
                    logger.info(f"Creating SYN protection '{protection_name}' at URL: {url}")
                    resp = cc._post(url, json=body)
                    try:
                        operation["response"] = resp.json()
                    except Exception:
                        operation["response"] = {"raw_text": resp.text}
                    refresh_device_state(cc, dp_ip, provider, logger)
                    changes_made = True
                    status = "success"
                except Exception as e:
                    err = f"Protection '{protection_name}' creation failed: {str(e)}"
                    errors.append(err)
                    operation["response"] = {"error": str(e)}
                    logger.error(err)
                    continue

            created_protections.append({
                'name': protection_name,
                'parameters': {
                    "activation_threshold": body["rsIDSSYNAttackActivationThreshold"],
                    "termination_threshold": body["rsIDSSYNAttackTerminationThreshold"],
                    "app_port_group": body["rsIDSSYNDestinationAppPortGroup"] or "all"
                },
                'status': status
            })

        # ---------------- SYN Profiles ----------------
        for profile in syn_profiles:
            profile_name = profile.get('name', 'unnamed_profile')
            protections = profile.get('protections', [])
            params = profile.get('params', {})

            attached = []
            for protection_name in protections:
                body_profile = {
                    "rsIDSSynProfilesName": profile_name,
                    "rsIDSSynProfileServiceName": protection_name
                }
                url_profile = (
                    f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}"
                    f"/config/rsIDSSynProfilesTable/{profile_name}/{protection_name}"
                )

                operation = {
                    "type": "profile_create",
                    "profile": profile_name,
                    "protection": protection_name,
                    "method": "POST",
                    "uri": url_profile,
                    "request_body": body_profile,
                    "response": None
                }
                debug_info['operations'].append(operation)

                if (profile_name, protection_name) in existing_attachments:
                    operation["method"] = "SKIP"
                    operation["response"] = {"status": "already_exists"}
                    attached.append(protection_name)
                else:
                    try:
                        logger.info(f"Attaching '{protection_name}' to SYN profile '{profile_name}'")
                        resp_profile = cc._post(url_profile, json=body_profile)
                        try:
                            operation["response"] = resp_profile.json()
                        except Exception:
                            operation["response"] = {"raw_text": resp_profile.text}
                        refresh_device_state(cc, dp_ip, provider, logger)
                        attached.append(protection_name)
                        changes_made = True
                    except Exception as e:
                        err = f"Profile '{profile_name}': failed to attach '{protection_name}': {str(e)}"
                        errors.append(err)
                        operation["response"] = {"error": str(e)}
                        logger.error(err)

            profile_entry = {
                'profile_name': profile_name,
                'protections': attached,
                'parameters': {},
                'skipped': {},
                'status': 'success'
            }

            if params:
                body_params, applied_params, skipped_params = map_syn_profile_parameters(profile_name, params)
                profile_entry['parameters'] = applied_params
                profile_entry['skipped'] = skipped_params

                for key, reason in skipped_params.items():
                    logger.debug(f"Profile '{profile_name}': {reason} for parameter '{key}'")

                url_params = (
                    f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}"
                    f"/config/rsIDSSynProfilesParamsTable/{profile_name}"
                )

                params_rows = get_table_rows(cc, provider, dp_ip, "rsIDSSynProfilesParamsTable")
                current_row = next(
                    (row for row in params_rows if row.get(PARAMS_NAME_FIELD) == profile_name),
                    None
                )
                request_body = merge_params_row(current_row, body_params)
                params_changed = current_row is None or any(
                    str(current_row.get(field)) != str(value)
                    for field, value in body_params.items()
                )

                operation = {
                    "type": "profile_params",
                    "profile": profile_name,
                    "method": ("PUT" if current_row else "POST") if params_changed else "SKIP",
                    "uri": url_params,
                    "request_body": request_body,
                    "skipped_parameters": skipped_params,
                    "response": None
                }
                debug_info['operations'].append(operation)

                if not params_changed:
                    operation["response"] = {"status": "already_configured"}
                else:
                    write_attempts = []
                    try:
                        logger.info(f"Applying complete parameter row for SYN profile '{profile_name}'")
                        logger.debug(f"{operation['method']} body: {request_body}")
                        effective_params = row_to_user_params(request_body)
                        data, strategy_used = write_params_row(
                            cc, bool(current_row), url_params, request_body,
                            effective_params, logger, write_attempts
                        )
                        operation["response"] = data
                        operation["write_strategy"] = strategy_used
                        operation["write_attempts"] = write_attempts
                        if strategy_used != "full_row":
                            logger.info(
                                f"Profile '{profile_name}': full-row write rejected by device; "
                                f"succeeded using '{strategy_used}' fallback"
                            )
                        refresh_device_state(cc, dp_ip, provider, logger)
                        changes_made = True
                    except Exception as params_error:
                        err = f"Profile '{profile_name}' parameters failed: {str(params_error)}"
                        errors.append(err)
                        operation["response"] = {
                            "error": str(params_error),
                            "write_attempts": write_attempts,
                            "device_params_table": describe_params_table(
                                cc, provider, dp_ip, profile_name, logger)
                        }
                        profile_entry['status'] = 'partial'
                        logger.error(err)

            created_profiles.append(profile_entry)

        result.update({
            'changed': changes_made,
            'response': {
                'created_protections': created_protections,
                'created_profiles': created_profiles,
                'errors': errors,
                'summary': {
                    'total_protections_attempted': len(syn_protections),
                    'protections_created': len(created_protections),
                    'total_profiles_attempted': len(syn_profiles),
                    'profiles_created': len([p for p in created_profiles if p['status'] == 'success']),
                    'errors_count': len(errors)
                }
            },
            'debug_info': debug_info
        })

        if errors:
            module.fail_json(msg=f"SYN configuration completed with {len(errors)} error(s).", **result)

        module.exit_json(**result)

    except Exception as e:
        result['debug_info'] = debug_info
        module.fail_json(msg=str(e), **result)


def describe_params_table(cc, provider, dp_ip, profile_name, logger):
    """Report the real table shape so a failed write shows the device's own column names."""
    url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesParamsTable"
    try:
        rows = cc._get(url).json().get("rsIDSSynProfilesParamsTable", [])
    except Exception as e:
        return {"error": str(e)}

    match = next((r for r in rows if r.get("rsIDSSynProfilesParamsName") == profile_name), None)
    logger.debug(f"Params table has {len(rows)} row(s); row for '{profile_name}' exists: {match is not None}")
    return {
        "row_count": len(rows),
        "row_exists_for_profile": match is not None,
        "row_for_profile": match,
        "device_column_names": sorted(rows[0]) if rows else []
    }


def get_table_rows(cc, provider, dp_ip, table_name):
    """Return rows from a DefensePro configuration table."""
    url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/{table_name}"
    payload = cc._get(url).json()
    rows = payload.get(table_name, [])
    return rows if isinstance(rows, list) else []


def refresh_device_state(cc, dp_ip, provider, logger):
    """Refresh device state to avoid API caching issues."""
    try:
        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable"
        resp = cc._get(url)
        logger.debug(f"Refreshed device state for {dp_ip} (status {resp.status_code})")
    except Exception as e:
        logger.debug(f"State refresh failed (non-critical): {str(e)}")


def main():
    run_module()


if __name__ == '__main__':
    main()
