from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: delete_syn_protection
short_description: Delete an IDS SYN Protection from a DefensePro device
description:
  - Deletes a SYN protection from a Radware DefensePro via Radware CC API.
  - Can delete using either human-readable name or numeric protection ID.
options:
  provider:
    type: dict
    required: true
  dp_ip:
    type: str
    required: true
  name:
    type: str
    required: false
    description: Name of the SYN protection (if protection_id not used)
  protection_id:
    type: int
    required: false
    description: Numeric protection ID (overrides name if provided)
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Delete SYN Protection by name
  delete_syn_protection:
    provider:
      server: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    name: "TEST"

- name: Delete SYN Protection by numeric ID
  delete_syn_protection:
    provider:
      server: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    protection_id: 500007
'''

RETURN = r'''
response:
  description: API response
  type: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=False),
        protection_id=dict(type='int', required=False),
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    protection_name = module.params.get('name')
    protection_id = module.params.get('protection_id')

    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['server'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        if not module.check_mode:
            # Determine URL based on ID or name
            if protection_id:
                path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/{protection_id}"
            elif protection_name:
                path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/{protection_name}"
            else:
                module.fail_json(msg="Either 'name' or 'protection_id' must be provided")

            url = f"https://{provider['server']}{path}"
            debug_info = {
                'method': 'DELETE',
                'url': url,
                'body': None
            }

            logger.info(f"Deleting SYN protection on device {dp_ip}")
            logger.debug(f"Request: {debug_info}")

            resp = cc._delete(url)
            logger.debug(f"Response status: {resp.status_code}")

            try:
                data = resp.json()
                logger.debug(f"Response JSON: {data}")
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
