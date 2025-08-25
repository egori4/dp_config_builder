from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

DOCUMENTATION = r'''
---
module: delete_cl_protection
short_description: Delete CL Protection on DefensePro
description:
  - Deletes a Connection Limit (CL) Protection from Radware DefensePro via CC API.
options:
  provider:
    description:
      - Dictionary with CC connection parameters
    type: dict
    required: true
    suboptions:
      server:
        description: CC IP address
        type: str
        required: true
      username:
        type: str
        required: true
      password:
        type: str
        required: true
  dp_ip:
    description: DefensePro device IP
    type: str
    required: true
  protection_name:
    description: Name of the CL protection to delete
    type: str
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Delete CL Protection
  delete_cl_protection:
    provider:
      server: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    protection_name: "Test_prot"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        protection_name=dict(type='str', required=True)
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']

    from ansible.module_utils.logger import Logger
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['server'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        if not module.check_mode:
            url = f"https://{provider['server']}/mgmt/device/byip/{module.params['dp_ip']}/config/rsCLProtectionTable/{module.params['protection_name']}"
            debug_info = {'method': 'DELETE', 'url': url}
            logger.info(f"Deleting CL Protection {module.params['protection_name']} on device {module.params['dp_ip']}")
            logger.debug(f"Request: {debug_info}")

            resp = cc._delete(url)
            logger.debug(f"Response status: {resp.status_code}")
            try:
                data = resp.json()
                logger.debug(f"Response JSON: {data}")
            except ValueError:
                data = {}
                logger.warning(f"Response is not JSON: {resp.text}")

            result['response'] = data
            result['changed'] = True
            debug_info['response_status'] = resp.status_code
            debug_info['response_json'] = data

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
