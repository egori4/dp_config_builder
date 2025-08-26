# plugins/modules/delete_syn_profile.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: delete_syn_profile
short_description: Delete a SYN Profile from a DefensePro device
options:
  provider:
    type: dict
    required: true
  dp_ip:
    type: str
    required: true
  profile_name:
    type: str
    required: true
  service_name:
    type: str
    required: true
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        profile_name=dict(type='str', required=True),
        service_name=dict(type='str', required=True)
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['server'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        if not module.check_mode:
            profile_name = module.params['profile_name']
            service_name = module.params['service_name']

            # Construct DELETE path with both profile and service as row index
            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsIDSSynProfilesTable/{profile_name}/{service_name}"
            url = f"https://{provider['server']}{path}"
            debug_info = {'method': 'DELETE', 'url': url, 'body': None}

            logger.info(f"Deleting SYN Profile {profile_name}/{service_name} on device {module.params['dp_ip']}")
            logger.debug(f"Request: {debug_info}")

            resp = cc._delete(url)
            resp.raise_for_status()  # Ensure HTTP errors are caught

            try:
                data = resp.json()
            except ValueError:
                raise Exception(f"Invalid JSON response: {resp.text}")

            result['response'] = data
            result['changed'] = True
            debug_info['response_status'] = resp.status_code
            debug_info['response_json'] = data

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
