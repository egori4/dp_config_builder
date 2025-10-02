# plugins/modules/manage_syn_configuration.py
"""
Unified Ansible module to manage DefensePro SYN protections and profiles.

- Handles both SYN protection creation and SYN profile creation.
- Provides structured results and full debug details (METHOD, URI, Response Code, Request Body, Response Data).
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

            for protection in syn_protections:
                protection_name = protection['name']
                index = protection.get('index', 0)
                body = {
                    "rsIDSSYNAttackName": protection_name,
                    "rsIDSSYNAttackActivationThreshold": protection.get("activation_threshold", 1000),
                    "rsIDSSYNAttackTerminationThreshold": protection.get("termination_threshold", 500),
                    "rsIDSSYNDestinationAppPortGroup": protection.get("app_port_group", "")
                }

                path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/{index}"
                url = f"https://{provider['cc_ip']}{path}"

                logger.info(f"Creating SYN protection '{protection_name}' at index {index}")
                resp = cc._post(url, json=body)

                try:
                    data = resp.json()
                except Exception:
                    data = {"raw_text": resp.text}

                created_protections.append({
                    'name': protection_name,
                    'index': index,
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

                    # Map human-friendly profile parameters
                    if "params" in profile:
                        for k, v in profile["params"].items():
                            api_key = FIELD_MAP.get(k, k)
                            api_value = VALUE_MAP.get(k, {}).get(v.lower(), v) if isinstance(v, str) else v
                            body[api_key] = api_value

                    path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesTable/{profile_name}/{protection_name}"
                    url = f"https://{provider['cc_ip']}{path}"

                    logger.info(f"Creating SYN profile '{profile_name}' with protection '{protection_name}'")
                    resp = cc._post(url, json=body)

                    try:
                        data = resp.json()
                    except Exception:
                        data = {"raw_text": resp.text}

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

        result['changed'] = changes_made
        result['response'] = {
            'protections': created_protections,
            'profiles': created_profiles
        }
        debug_info['summary'] = {
            'protections_created': len(created_protections),
            'profiles_created': len(created_profiles),
            'operations_completed': changes_made
        }

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
