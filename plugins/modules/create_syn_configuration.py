# plugins/modules/manage_syn_configuration.py
"""
Unified Ansible module to manage DefensePro SYN protections and profiles.

- Handles both SYN protection creation and SYN profile creation.
- Provides structured results, summary, and full debug details.
"""

from ansible.module_utils.basic import AnsibleModule


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

    # Log input parameters
    logger.debug(f"Module input: dp_ip={dp_ip}, protections_count={len(syn_protections)}, profiles_count={len(syn_profiles)}")

    debug_info['input'] = {
        'dp_ip': dp_ip,
        'protections_count': len(syn_protections),
        'profiles_count': len(syn_profiles)
    }

    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'],
                       provider['password'], log_level=log_level, logger=logger)

        changes_made = False
        created_protections = []
        created_profiles = []

        if not module.check_mode:

            # Create SYN protections
            for protection in syn_protections:
                protection_name = protection['name']
                body = {
                    "rsIDSSYNAttackName": protection_name,
                    "rsIDSSYNAttackActivationThreshold": protection.get("activation_threshold", 1000),
                    "rsIDSSYNAttackTerminationThreshold": protection.get("termination_threshold", 500),
                    "rsIDSSYNDestinationAppPortGroup": protection.get("app_port_group", "")
                }

                path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/0"
                url = f"https://{provider['cc_ip']}{path}"

                logger.info(f"Creating SYN protection '{protection_name}'")
                logger.debug(f"SYN protection POST URL: {url}, Body: {body}")
                resp = cc._post(url, json=body)

                try:
                    data = resp.json()
                except Exception:
                    data = {"raw_text": resp.text}

                # Log response
                logger.debug(f"SYN protection '{protection_name}' response: {data}")

                # Append protection without 'index' in response
                created_protections.append({
                    'name': protection_name,
                    'parameters': {
                        "activation_threshold": body["rsIDSSYNAttackActivationThreshold"],
                        "termination_threshold": body["rsIDSSYNAttackTerminationThreshold"],
                        "app_port_group": body["rsIDSSYNDestinationAppPortGroup"],
                    },
                    'request': {"method": "POST", "uri": url, "body": body},
                    'response_code': resp.status_code,
                    'raw_response': data
                })

                debug_info['operations'].append({
                    "type": "protection_create",
                    "name": protection_name,
                    "method": "POST",
                    "uri": url,
                    "request_body": body,
                    "status_code": resp.status_code,
                    "response": data
                })

                changes_made = True
                refresh_device_state(cc, dp_ip, provider, logger)

            # Create SYN profiles
            FIELD_MAP = {"profile_type": "rsIDSSynProfileType"}
            VALUE_MAP = {"profile_type": {"syn_protection": 4}}

            for profile in syn_profiles:
                profile_name = profile['name']
                protections = profile.get('protections', [])

                for protection_name in protections:
                    body = {
                        "rsIDSSynProfilesName": profile_name,
                        "rsIDSSynProfileServiceName": protection_name
                    }

                    if "params" in profile:
                        for k, v in profile["params"].items():
                            api_key = FIELD_MAP.get(k, k)
                            api_value = VALUE_MAP.get(k, {}).get(v.lower(), v) if isinstance(v, str) else v
                            body[api_key] = api_value

                    path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesTable/{profile_name}/{protection_name}"
                    url = f"https://{provider['cc_ip']}{path}"

                    logger.info(f"Creating SYN profile '{profile_name}' with protection '{protection_name}'")
                    logger.debug(f"SYN profile POST URL: {url}, Body: {body}")
                    resp = cc._post(url, json=body)

                    try:
                        data = resp.json()
                    except Exception:
                        data = {"raw_text": resp.text}

                    logger.debug(f"SYN profile '{profile_name}' response: {data}")

                    created_profiles.append({
                        'profile_name': profile_name,
                        'protection_name': protection_name,
                        'parameters': profile.get("params", {}),
                        'request': {"method": "POST", "uri": url, "body": body},
                        'response_code': resp.status_code,
                        'raw_response': data
                    })

                    debug_info['operations'].append({
                        "type": "profile_create",
                        "profile": profile_name,
                        "protection": protection_name,
                        "method": "POST",
                        "uri": url,
                        "request_body": body,
                        "status_code": resp.status_code,
                        "response": data
                    })

                    changes_made = True
                    refresh_device_state(cc, dp_ip, provider, logger)

        protections_created_count = len(created_protections)
        profiles_created_count = len(created_profiles)

        result['changed'] = changes_made
        result['response'] = {
            'protections': created_protections,
            'profiles': created_profiles,
            'summary': {
                'total_protections_attempted': protections_created_count,
                'total_profiles_attempted': profiles_created_count,
                'protections_created': protections_created_count,
                'profiles_created': profiles_created_count,
                'operations_completed': changes_made
            }
        }

        # Log final summary
        logger.debug(f"Module execution summary: {result['response']['summary']}")
        debug_info['summary'] = result['response']['summary']

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def refresh_device_state(cc, dp_ip, provider, logger):
    """Refresh device state to avoid API caching issues."""
    try:
        path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable"
        url = f"https://{provider['cc_ip']}{path}"
        resp = cc._get(url)
        logger.debug(f"Refreshed device state for {dp_ip} (status {resp.status_code})")
    except Exception as e:
        logger.debug(f"State refresh failed (non-critical): {str(e)}")


def main():
    run_module()


if __name__ == '__main__':
    main()
