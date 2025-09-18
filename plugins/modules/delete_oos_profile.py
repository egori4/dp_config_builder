# plugins/modules/delete_oos_profile.py
"""
Ansible module to delete OOS profiles on Radware DefensePro devices,
with verification to ensure the profile is actually removed.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: dp_delete_oos_profile
short_description: Delete OOS/Stateful profile on Radware DefensePro
description:
  - Deletes an OOS/Stateful profile on a DefensePro device.
  - Confirms deletion by verifying the profile no longer exists.
options:
  provider:
    type: dict
    required: true
  dp_ip:
    type: str
    required: true
  name:
    type: str
    required: true
'''

EXAMPLES = r'''
- name: Delete OOS profile from a device
  dp_delete_oos_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: radware
    dp_ip: 10.105.192.32
    name: Test1
'''

RETURN = r'''
changed:
  description: Whether the profile was deleted
  type: bool
response:
  description: Raw API response from delete and verification
  type: dict
debug_info:
  description: Debugging information
  type: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=True)
    )

    result = dict(changed=False, response={}, debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    profile_name = module.params['name']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    debug_info = {}

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        path = f"/mgmt/device/byip/{dp_ip}/config/rsStatefulProfileTable/{profile_name}"
        url = f"https://{provider['cc_ip']}{path}"

        debug_info['delete_request'] = {'method': 'DELETE', 'url': url}
        logger.info(f"Deleting OOS/Stateful profile '{profile_name}' on {dp_ip}")

        if module.check_mode:
            result['changed'] = True
            module.exit_json(msg=f"Check mode: profile '{profile_name}' would be deleted.", **result)

        # Send DELETE request
        resp = cc._delete(url)
        debug_info['delete_status_code'] = resp.status_code

        try:
            resp_data = resp.json()
        except ValueError:
            resp_data = {'raw_text': resp.text}
        debug_info['delete_response'] = resp_data

        if resp.status_code not in (200, 201):
            module.fail_json(msg=f"Failed to delete profile '{profile_name}': HTTP {resp.status_code}", debug_info=debug_info, **result)

        # Verify deletion
        verify_path = f"/mgmt/device/byip/{dp_ip}/config/rsStatefulProfileTable"
        verify_url = f"https://{provider['cc_ip']}{verify_path}"
        verify_resp = cc._get(verify_url)
        debug_info['verify_status_code'] = verify_resp.status_code
        try:
            verify_data = verify_resp.json()
        except ValueError:
            verify_data = {'raw_text': verify_resp.text}
        debug_info['verify_response'] = verify_data

        existing_profiles = verify_data.get('rsStatefulProfileTable', [])
        if any(p.get('rsStatefulProfileName') == profile_name for p in existing_profiles):
            module.fail_json(msg=f"Profile '{profile_name}' still exists after deletion!", debug_info=debug_info, **result)

        logger.info(f"Profile '{profile_name}' deleted successfully")
        result['changed'] = True
        result['response'] = resp_data

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
