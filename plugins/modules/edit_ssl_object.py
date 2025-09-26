#!/usr/bin/python
"""
Unified Ansible module to edit Protected SSL Objects on DefensePro via Radware CyberController API.

- Supports multiple SSL objects
- User-friendly enable/disable mapping
- Detailed results and check mode
"""

from ansible.module_utils.basic import AnsibleModule

ENABLE_MAP = {
    "enable": "1",
    "disable": "2"
}

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        edit_ssl_objects=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    edit_ssl_objects = module.params['edit_ssl_objects']

    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    debug_info['input'] = {
        'dp_ip': dp_ip,
        'edit_ssl_objects_count': len(edit_ssl_objects)
    }

    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'],
                       provider['password'], log_level=log_level, logger=logger)

        changes_made = False
        edited_objects = []
        errors = []

        if not module.check_mode:
            for ssl in edit_ssl_objects:
                name = ssl.get('ssl_object_name', '')
                ip = ssl.get('ip_address', '')
                port = ssl.get('Port', 443)

                if not name or not ip:
                    error_msg = f"SSL edit missing required 'ssl_object_name' or 'ip_address'"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    continue

                # Prepare body for API
                body = {
                    "rsProtectedObjEnable": ENABLE_MAP.get(ssl.get('ssl_object_profile', 'enable'), '1'),
                    "rsProtectedObjIpAddr": ip,
                    "rsProtectedObjApplPort": port,
                    "rsProtectedObjAddCertificate": ssl.get('add_certificate', ''),
                    "rsProtectedObjRemoveCertificate": ssl.get('remove_certificate', ''),
                    "rsProtectedObjSSLV3Enable": ENABLE_MAP.get(ssl.get('front_sslv3', 'disable'), '2'),
                    "rsProtectedObjTLS10Enable": ENABLE_MAP.get(ssl.get('front_tls1.0', 'disable'), '2'),
                    "rsProtectedObjTLS11Enable": ENABLE_MAP.get(ssl.get('front_tls1.1', 'enable'), '1'),
                    "rsProtectedObjTLS12Enable": ENABLE_MAP.get(ssl.get('front_tls1.2', 'enable'), '1'),
                    "rsProtectedObjTLS13Enable": ENABLE_MAP.get(ssl.get('front_tls1.3', 'enable'), '1'),
                    "rsBEDecryptionEnable": ENABLE_MAP.get(ssl.get('bk_end_decrypt', 'enable'), '1'),
                    "rsBEProtectedObjSSLV3Enable": ENABLE_MAP.get(ssl.get('bk_end_sslv3', 'disable'), '2'),
                    "rsBEProtectedObjTLS10Enable": ENABLE_MAP.get(ssl.get('bk_end_tls1.0', 'disable'), '2'),
                    "rsBEProtectedObjTLS11Enable": ENABLE_MAP.get(ssl.get('bk_end_tls1.1', 'enable'), '1'),
                    "rsBEProtectedObjTLS12Enable": ENABLE_MAP.get(ssl.get('bk_end_tls1.2', 'enable'), '1'),
                    "rsBEProtectedObjTLS13Enable": ENABLE_MAP.get(ssl.get('bk_end_tls1.3', 'enable'), '1'),
                    "rsBEL4PortNumber": ssl.get('bk_end_port', '')
                }

                try:
                    path = f"/mgmt/device/byip/{dp_ip}/config/rsProtectedSslObjTable/{name}"
                    url = f"https://{provider['cc_ip']}{path}"

                    logger.info(f"Editing SSL object '{name}' ({ip}:{port})")
                    logger.debug(f"Request URL: {url}")
                    logger.debug(f"Request body: {body}")

                    resp = cc._put(url, json=body)
                    data = resp.json()

                    edited_objects.append({
                        'ssl_object_name': name,
                        'parameters': ssl,
                        'status': 'success',
                        'response': data
                    })
                    changes_made = True
                    logger.info(f"Successfully edited SSL object '{name}'")

                except Exception as e:
                    error_msg = f"Failed to edit SSL object '{name}' ({ip}:{port}): {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    edited_objects.append({
                        'ssl_object_name': name,
                        'parameters': ssl,
                        'status': 'failed',
                        'error': str(e)
                    })

            result['changed'] = changes_made
            result['response'] = {
                'edited_objects': edited_objects,
                'errors': errors,
                'summary': {
                    'total_objects_attempted': len(edited_objects),
                    'successful_edits': len([o for o in edited_objects if o['status'] == 'success']),
                    'failed_edits': len([o for o in edited_objects if o['status'] == 'failed'])
                }
            }

        else:
            # Check mode
            planned_operations = []
            for ssl in edit_ssl_objects:
                name = ssl.get('ssl_object_name', '')
                ip = ssl.get('ip_address', '')
                port = ssl.get('Port', 443)
                if not name or not ip:
                    errors.append(f"SSL edit missing 'ssl_object_name' or 'ip_address'")
                    continue
                planned_operations.append({
                    'ssl_object_name': name,
                    'ip_address': ip,
                    'Port': port,
                    'description': f"Edit SSL object '{name}' ({ip}:{port})"
                })

            result['changed'] = bool(planned_operations)
            result['response'] = {
                'preview_mode': True,
                'planned_operations': planned_operations,
                'total_operations': len(planned_operations)
            }

        if errors:
            if not result.get('changed', False):
                module.fail_json(msg=f"All operations failed. Errors: {'; '.join(errors)}", debug_info=debug_info, **result)
            else:
                result['warnings'] = errors

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
