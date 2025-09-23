# plugins/modules/get_ssl_object.py
"""
Ansible module to fetch Protected SSL Objects on Radware DefensePro via CyberController API.

- Retrieves all SSL objects from a DefensePro device.
- Maps API response values back to user-friendly keys (enable/disable for flags).
- Returns structured response with raw, formatted, and summary data.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC

ENABLE_DISABLE_MAP = {"1": "enable", "2": "disable"}

def format_ssl_object_for_display(raw_obj):
    """
    Convert raw SSL object API data to user-friendly format.
    """
    formatted = {
        "ssl_object_profile": ENABLE_DISABLE_MAP.get(raw_obj.get("rsProtectedObjEnable"), raw_obj.get("rsProtectedObjEnable")),
        "IP_Address": raw_obj.get("rsProtectedObjIpAddr"),
        "Port": raw_obj.get("rsProtectedObjApplPort"),
        "add_certificate": raw_obj.get("rsProtectedObjAddCertificate"),
        "remove_certificate": raw_obj.get("rsProtectedObjRemoveCertificate"),
        "front_sslv3": ENABLE_DISABLE_MAP.get(raw_obj.get("rsProtectedObjSSLV3Enable")),
        "front_tls1.0": ENABLE_DISABLE_MAP.get(raw_obj.get("rsProtectedObjTLS10Enable")),
        "front_tls1.1": ENABLE_DISABLE_MAP.get(raw_obj.get("rsProtectedObjTLS11Enable")),
        "front_tls1.2": ENABLE_DISABLE_MAP.get(raw_obj.get("rsProtectedObjTLS12Enable")),
        "front_tls1.3": ENABLE_DISABLE_MAP.get(raw_obj.get("rsProtectedObjTLS13Enable")),
        "cipher_suite": ENABLE_DISABLE_MAP.get(raw_obj.get("rsProtectedObjCipherSuiteSystemEnable")),
        "UserCipher": raw_obj.get("rsProtectedObjUserCipher"),
        "bk_end_dcrypt": ENABLE_DISABLE_MAP.get(raw_obj.get("rsBEDecryptionEnable")),
        "bk_end_sslv3": ENABLE_DISABLE_MAP.get(raw_obj.get("rsBEProtectedObjSSLV3Enable")),
        "bk_end_tls1.0": ENABLE_DISABLE_MAP.get(raw_obj.get("rsBEProtectedObjTLS10Enable")),
        "bk_end_tls1.1": ENABLE_DISABLE_MAP.get(raw_obj.get("rsBEProtectedObjTLS11Enable")),
        "bk_end_tls1.2": ENABLE_DISABLE_MAP.get(raw_obj.get("rsBEProtectedObjTLS12Enable")),
        "bk_end_tls1.3": ENABLE_DISABLE_MAP.get(raw_obj.get("rsBEProtectedObjTLS13Enable")),
        "bk_cipher": ENABLE_DISABLE_MAP.get(raw_obj.get("rsBEProtectedObjCipherSuiteSystemEnable")),
        "bk_user_cipher": raw_obj.get("rsBEProtectedObjUserCipher"),
        "bk_end_port": raw_obj.get("rsBEL4PortNumber")
    }
    return formatted

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        filter_ssl_names=dict(type='list', required=False, default=[])
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    filter_ssl_names = module.params['filter_ssl_names']

    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                   log_level=log_level, logger=logger)

    try:
        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsProtectedSslObjTable"
        logger.info(f"Fetching SSL objects from device {dp_ip}")
        resp = cc._get(url)
        data = resp.json()

        ssl_objects_raw = data.get('rsProtectedSslObjTable', [])
        debug_info['ssl_objects_raw_count'] = len(ssl_objects_raw)

        # Apply filter if provided
        if filter_ssl_names:
            ssl_objects_raw = [o for o in ssl_objects_raw if o.get('rsProtectedObjName') in filter_ssl_names]
            logger.info(f"Filtered SSL objects to: {filter_ssl_names}")

        formatted_objects = {}
        objects_summary = {}

        for obj in ssl_objects_raw:
            obj_name = obj.get('rsProtectedObjName')
            if not obj_name:
                continue
            if obj_name not in formatted_objects:
                formatted_objects[obj_name] = []
                objects_summary[obj_name] = []
            formatted_objects[obj_name].append(format_ssl_object_for_display(obj))
            objects_summary[obj_name].append(obj)

        result['response'] = {
            'rsProtectedSslObjTable': ssl_objects_raw,
            'formatted_objects': formatted_objects,
            'summary': {
                'total_entries': len(ssl_objects_raw),
                'unique_ssl_objects': len(formatted_objects),
                'ssl_names': list(formatted_objects.keys()),
                'filtered': bool(filter_ssl_names),
                'filter_applied': filter_ssl_names if filter_ssl_names else None
            },
            'objects_breakdown': objects_summary
        }

        debug_info['summary'] = {
            'total_entries_retrieved': len(ssl_objects_raw),
            'unique_objects_found': len(formatted_objects),
            'filter_applied': bool(filter_ssl_names),
            'ssl_names_found': list(formatted_objects.keys())
        }

        result['debug_info'] = debug_info
        module.exit_json(**result)

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

def main():
    run_module()

if __name__ == '__main__':
    main()
