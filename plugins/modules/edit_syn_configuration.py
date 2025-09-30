# plugins/modules/edit_syn_protection.py
"""
Unified Ansible module to edit DefensePro SYN protections and attach protections to SYN profiles.

- Edits existing SYN protections (partial update supported)
- Attaches protections to SYN profiles (multi-attach)
- Provides user-friendly debug info and logging
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

def run_module():
    PACKET_REPORT_MAP = {"enable": 1, "disable": 2}

    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        edit_syn_protections=dict(type='list', required=False, default=[]),
        edit_syn_profiles=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, results=[], debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    edit_syn_protections = module.params['edit_syn_protections']
    edit_syn_profiles = module.params['edit_syn_profiles']

    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'], log_level=log_level, logger=logger)

    any_changed = False
    debug_info = {'device': dp_ip, 'protections': [], 'profiles': []}

    try:
        # ---------------------------
        # Step 1: Edit SYN protections
        # ---------------------------
        for prot in edit_syn_protections:
            prot_result = dict(changed=False, response={}, debug_info={})
            body = {}

            prot_index = prot.get('index')
            if prot_index is None:
                prot_result['debug_info'] = {'error': 'Missing protection index'}
                result['results'].append(prot_result)
                continue

            if 'activation_threshold' in prot:
                body['rsIDSSYNAttackActivationThreshold'] = prot['activation_threshold']
            if 'termination_threshold' in prot:
                body['rsIDSSYNAttackTerminationThreshold'] = prot['termination_threshold']
            if 'app_port_group' in prot:
                body['rsIDSSYNDestinationAppPortGroup'] = prot['app_port_group']
            if 'packet_report' in prot:
                body['rsIDSSYNAttackPacketReport'] = PACKET_REPORT_MAP.get(prot['packet_report'], 2)

            if not body:
                prot_result['debug_info'] = {'error': 'No parameters to update'}
                result['results'].append(prot_result)
                continue

            path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/{prot_index}"
            url = f"https://{provider['cc_ip']}{path}"
            prot_result['debug_info'] = {'method': 'PUT', 'url': url, 'body': body}

            logger.info(f"Editing SYN protection {prot_index} on device {dp_ip}")
            logger.debug(f"PUT URL: {url}, body: {body}")

            try:
                if not module.check_mode:
                    resp = cc._put(url, json=body)
                    prot_result['response'] = resp.json()
                    prot_result['changed'] = True
                    any_changed = True
                    logger.info(f"Edited SYN protection {prot_index} successfully")
                    logger.debug(f"Response: {prot_result['response']}")
            except Exception as e:
                prot_result['debug_info']['error'] = str(e)
                logger.error(f"Failed to edit SYN protection {prot_index}: {str(e)}")

            result['results'].append(prot_result)
            debug_info['protections'].append(prot_result['debug_info'])

        # ----------------------------------------
        # Step 2: Attach protections to SYN profiles
        # ----------------------------------------
        for profile in edit_syn_profiles:
            profile_name = profile['name']
            protections = profile.get('protections', [])

            for protection_name in protections:
                prof_result = dict(changed=False, response={}, debug_info={})
                body = {
                    "rsIDSSynProfilesName": profile_name,
                    "rsIDSSynProfileServiceName": protection_name
                }

                path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesTable/{profile_name}/{protection_name}"
                url = f"https://{provider['cc_ip']}{path}"
                prof_result['debug_info'] = {'method': 'POST', 'url': url, 'body': body}

                logger.info(f"Attaching protection {protection_name} to SYN profile {profile_name} on device {dp_ip}")
                logger.debug(f"POST URL: {url}, body: {body}")

                try:
                    if not module.check_mode:
                        resp = cc._post(url, json=body)
                        prof_result['response'] = resp.json()
                        prof_result['changed'] = True
                        any_changed = True
                        logger.info(f"Attached protection {protection_name} to profile {profile_name}")
                        logger.debug(f"Response: {prof_result['response']}")
                except Exception as e:
                    prof_result['debug_info']['error'] = str(e)
                    logger.error(f"Failed to attach protection {protection_name} to profile {profile_name}: {str(e)}")

                result['results'].append(prof_result)
                debug_info['profiles'].append(prof_result['debug_info'])

        result['changed'] = any_changed
        result['debug_info'] = debug_info

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
