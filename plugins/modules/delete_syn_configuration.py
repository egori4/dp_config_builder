"""
Ansible module to delete DefensePro SYN profiles and protections.

Features:
- Remove protections from profiles
- Delete protections entirely
- Provides structured debug info including METHOD, URI, and response status
- Compatible with check mode for dry-run
- Returns summary of total attempted, deleted, and failed
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger
from ansible.module_utils.radware_cc import RadwareCC


def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        syn_profile_deletions=dict(type='list', required=False, default=[]),
        syn_protection_deletions=dict(type='list', required=False, default=[])
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    syn_profile_deletions = module.params['syn_profile_deletions']
    syn_protection_deletions = module.params['syn_protection_deletions']

    log_level = provider.get('log_level', 'disabled')
    verify_ssl = provider.get('verify_ssl', False)
    cc_ip = provider.get('cc_ip')
    username = provider.get('username')
    password = provider.get('password')

    if not all([cc_ip, username, password]):
        module.fail_json(msg="provider.cc_ip, provider.username, and provider.password are required")

    logger = Logger(verbosity=log_level)
    debug_info = {
        'input': {
            'dp_ip': dp_ip,
            'profile_deletions_count': len(syn_profile_deletions),
            'protection_deletions_count': len(syn_protection_deletions)
        },
        'operations': []
    }

    try:
        cc = RadwareCC(cc_ip, username, password, verify_ssl=verify_ssl, log_level=log_level, logger=logger)

        protection_name_to_id = {}
        try:
            resp = cc._get(f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable")
            resp.raise_for_status()
            for prot in resp.json().get('rsIDSSYNAttackTable', []):
                name = prot.get('rsIDSSYNAttackName')
                pid = prot.get('rsIDSSYNAttackId')
                if name and pid:
                    protection_name_to_id[name] = pid
            logger.info(f"Fetched {len(protection_name_to_id)} SYN protections from {dp_ip}")
        except Exception as e:
            module.fail_json(msg=f"Failed to fetch SYN protections: {str(e)}", debug_info=debug_info)

        operations = []

        for profile in syn_profile_deletions:
            profile_name = profile.get('profile_name')
            protections = profile.get('protections', [])
            for prot in protections:
                prot_name = prot.get('protection_name')
                prot_id = protection_name_to_id.get(prot_name)
                operations.append({
                    'type': 'remove_from_profile',
                    'profile_name': profile_name,
                    'protection_name': prot_name,
                    'method': 'DELETE',
                    'url': f"/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesTable/{profile_name}/{prot_name}",
                    'description': f"Remove '{prot_name}' from profile '{profile_name}'",
                    'exists': prot_id is not None
                })

        for prot_del in syn_protection_deletions:
            for prot_name in prot_del.get('protections_to_delete', []):
                prot_id = protection_name_to_id.get(prot_name)
                operations.append({
                    'type': 'delete_protection',
                    'protection_name': prot_name,
                    'protection_id': prot_id,
                    'method': 'DELETE',
                    'url': f"/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/{prot_id if prot_id else 'NA'}",
                    'description': f"Delete protection '{prot_name}' (ID {prot_id})",
                    'exists': prot_id is not None
                })

        deleted_from_profiles = []
        deleted_protections = []
        failed_operations = []
        changes_made = False

        for op in operations:
            debug_info['operations'].append(op)
            if not op.get('exists', True):
                failed_operations.append({
                    'object_name': op.get('protection_name'),
                    'status': 'FAILED',
                    'error': f"Object '{op.get('protection_name')}' not found",
                    'response_body': {}
                })
                continue

            try:
                if module.check_mode:
                    changes_made = True
                    continue
                resp = cc._delete(f"https://{cc_ip}{op['url']}")
                resp.raise_for_status()
                changes_made = True
                if op['type'] == 'remove_from_profile':
                    deleted_from_profiles.append({
                        'profile_name': op['profile_name'],
                        'protection_name': op['protection_name'],
                        'status': 'success'
                    })
                else:
                    deleted_protections.append({
                        'protection_name': op['protection_name'],
                        'protection_id': op['protection_id'],
                        'status': 'success'
                    })
                logger.info(f"Executed: {op['description']}")
            except Exception as e:
                failed_operations.append({
                    'object_name': op.get('protection_name'),
                    'status': 'FAILED',
                    'error': str(e),
                    'response_body': getattr(e, 'response', {})
                })
                logger.error(f"Failed: {op['description']}")

        # Prepare final result including summary
        total_attempted = len(operations)
        total_deleted = len(deleted_from_profiles) + len(deleted_protections)
        total_failed = len(failed_operations)

        result = {
            'changed': changes_made,
            'response': {
                'deleted_from_profiles': deleted_from_profiles,
                'deleted_protections': deleted_protections,
                'failed_operations': failed_operations,
                'summary': {
                    'total_attempted': total_attempted,
                    'total_deleted': total_deleted,
                    'total_failed': total_failed
                }
            },
            'debug_info': debug_info
        }

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info)


def main():
    run_module()


if __name__ == '__main__':
    main()
