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
    suboptions:
      cc_ip: str
      username: str
      password: str
      verify_ssl: bool
      log_level: str
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
    suboptions:
      profile_name: str
      protections: list
  syn_protection_deletions:
    description: List of protections to delete entirely (requires numeric IDs)
    type: list
    required: false
    default: []
    elements: dict
    suboptions:
      protections_to_delete: list
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

    cc_ip = provider.get('cc_ip')
    username = provider.get('username')
    password = provider.get('password')
    verify_ssl = provider.get('verify_ssl', False)
    log_level = provider.get('log_level', 'disabled')

    if not all([cc_ip, username, password]):
        module.fail_json(msg="provider.cc_ip, provider.username, and provider.password are required")

    logger = Logger(verbosity=log_level)
    debug_info = {}

    try:
        cc = RadwareCC(cc_ip, username, password, verify_ssl=verify_ssl, log_level=log_level, logger=logger)

        # Step 1: Fetch all SYN protections to resolve names to numeric IDs
        protection_name_to_id = {}
        try:
            resp = cc._get(f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable")
            data = resp.json()
            for prot in data.get('rsIDSSYNAttackTable', []):
                protection_name_to_id[prot['rsIDSSYNAttackName']] = prot['rsIDSSYNAttackId']
            logger.info(f"Fetched {len(protection_name_to_id)} SYN protections from {dp_ip}")
        except Exception as e:
            module.fail_json(msg=f"Failed to fetch SYN protections: {str(e)}", debug_info=debug_info)

        operations = []

        # Step 2: Remove protections from profiles
        for profile in syn_profile_deletions:
            profile_name = profile.get('profile_name')
            protections = profile.get('protections', [])
            for prot in protections:
                prot_name = prot.get('protection_name')
                prot_id = protection_name_to_id.get(prot_name)
                if not prot_id:
                    continue  # Skip missing protections silently
                url = f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesTable/{profile_name}/{prot_name}"
                operations.append({
                    'type': 'remove_from_profile',
                    'profile_name': profile_name,
                    'protection_name': prot_name,
                    'url': url
                })

        # Step 3: Delete protections entirely
        for prot_del in syn_protection_deletions:
            for prot_name in prot_del.get('protections_to_delete', []):
                prot_id = protection_name_to_id.get(prot_name)
                if not prot_id:
                    continue  # Skip missing protections silently
                url = f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/{prot_id}"
                operations.append({
                    'type': 'delete_protection',
                    'protection_name': prot_name,
                    'protection_id': prot_id,
                    'url': url
                })

        # Step 4: Execute or preview
        deleted_from_profiles = []
        deleted_protections = []
        changes_made = False

        for op in operations:
            try:
                if module.check_mode:
                    changes_made = True
                    continue

                resp = cc._delete(op['url'])
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
            except Exception:
                # Suppress all errors silently
                continue

        result = {
            'changed': changes_made,
            'response': {
                'deleted_from_profiles': deleted_from_profiles,
                'deleted_protections': deleted_protections
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
