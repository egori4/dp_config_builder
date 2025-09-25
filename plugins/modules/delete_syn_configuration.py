# plugins/modules/delete_syn_profile.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: delete_syn_profile
short_description: Delete SYN Profiles and Protections from a DefensePro device
description:
  - Deletes SYN profiles and/or protections from a DefensePro device via Radware CC API.
options:
  provider:
    description: Radware CC connection details
    type: dict
    required: true
  dp_ip:
    description: DefensePro device IP
    type: str
    required: true
  syn_profile_deletions:
    description: List of profiles and their attached protections to remove
    type: list
    required: false
    default: []
    elements: dict
  syn_protection_deletions:
    description: List of protections to delete entirely
    type: list
    required: false
    default: []
    elements: dict
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Delete SYN Profiles and Protections
  delete_syn_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
      verify_ssl: false
      log_level: debug
    dp_ip: 10.105.192.32
    syn_profile_deletions:
      - profile_name: "SYN_PROFILE_1"
        protections:
          - protection_name: "SYN_PROT_1"
          - protection_name: "SYN_PROT_2"
    syn_protection_deletions:
      - protections_to_delete:
          - "SYN_PROT_1"
          - "SYN_PROT_2"
'''

RETURN = r'''
response:
  description: API response
  type: dict
debug_info:
  description: Debug information for request/response
  type: dict
'''

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
    debug_info = {'input': {'dp_ip': dp_ip,
                            'profile_deletions_count': len(syn_profile_deletions),
                            'protection_deletions_count': len(syn_protection_deletions)}}

    try:
        cc = RadwareCC(cc_ip, username, password, verify_ssl=verify_ssl, log_level=log_level, logger=logger)

        # Step 1: Fetch all SYN protections for name → ID resolution
        protection_name_to_id = {}
        valid_ids = set()
        try:
            resp = cc._get(f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable")
            data = resp.json()
            for prot in data.get('rsIDSSYNAttackTable', []):
                name = prot.get('rsIDSSYNAttackName')
                pid = prot.get('rsIDSSYNAttackId')
                if name and pid:
                    protection_name_to_id[name] = pid
                    try:
                        valid_ids.add(int(pid))
                    except Exception:
                        pass
            logger.info(f"Fetched {len(protection_name_to_id)} SYN protections from {dp_ip}")
        except Exception as e:
            if not module.check_mode:
                module.fail_json(msg=f"Failed to fetch SYN protections: {str(e)}", debug_info=debug_info)

        operations = []
        errors = []

        # Step 2: Prepare profile removals
        for profile in syn_profile_deletions:
            profile_name = profile.get('profile_name')
            protections = profile.get('protections', [])
            for prot in protections:
                prot_name = prot.get('protection_name')
                prot_id = protection_name_to_id.get(prot_name)
                if not prot_id:
                    errors.append(f"Protection '{prot_name}' not found on device {dp_ip}")
                    continue
                operations.append({
                    'type': 'remove_from_profile',
                    'profile_name': profile_name,
                    'protection_name': prot_name,
                    'url_path': f"/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesTable/{profile_name}/{prot_name}",
                    'description': f"Remove '{prot_name}' from profile '{profile_name}'"
                })

        # Step 3: Prepare protection deletions
        for prot_del in syn_protection_deletions:
            for prot_name in prot_del.get('protections_to_delete', []):
                prot_id = protection_name_to_id.get(prot_name)
                if not prot_id:
                    errors.append(f"Protection '{prot_name}' not found on device {dp_ip}")
                    continue
                operations.append({
                    'type': 'delete_protection',
                    'protection_name': prot_name,
                    'protection_id': prot_id,
                    'url_path': f"/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/{prot_id}",
                    'description': f"Delete protection '{prot_name}' (ID {prot_id})"
                })

        # Step 4: Execute or preview
        deleted_from_profiles = []
        deleted_protections = []
        changes_made = False

        for op in operations:
            if op.get('error'):
                continue
            try:
                if module.check_mode:
                    changes_made = True
                    continue
                resp = cc._delete(f"https://{cc_ip}{op['url_path']}")
                resp.raise_for_status()
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
                changes_made = True
                logger.info(f"Executed: {op['description']}")
            except Exception as e:
                errors.append(f"Failed to execute {op['description']}: {str(e)}")
                logger.error(f"Failed: {op['description']}")

        result = {
            'changed': changes_made,
            'response': {
                'deleted_from_profiles': deleted_from_profiles,
                'deleted_protections': deleted_protections,
                'errors': errors
            },
            'debug_info': debug_info
        }

        if errors and not module.check_mode:
            if not changes_made:
                module.fail_json(msg=f"All operations failed. Errors: {'; '.join(errors)}", **result)

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info)


def main():
    run_module()


if __name__ == '__main__':
    main()
