# plugins/modules/dp_bdos_profile_delete.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

DOCUMENTATION = r'''
---
module: dp_bdos_profile_delete
short_description: Delete a DefensePro BDOS Flood profile
description:
  - Deletes a BDOS Flood profile on Radware DefensePro via Radware CC API.
options:
  provider:
    description:
      - Dictionary with connection parameters.
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
  name:
    description: Name of the BDOS Flood profile to delete
    type: str
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Delete BDOS Flood profile
  dp_bdos_profile_delete:
    provider:
      server: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    name: "BDOS_Test"
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
        name=dict(type='str', required=True)
    )

    result = dict(changed=False, response={})
    debug_info = {}

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    name = module.params['name']
    log_level = provider.get('log_level', 'disabled')

    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['server'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        path = f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{name}/"
        url = f"https://{provider['server']}{path}"
        debug_info['request'] = {"method": "DELETE", "url": url}
        logger.info(f"Deleting BDOS Flood profile '{name}' on {dp_ip}")

        if not module.check_mode:
            resp = cc._delete(url)
            debug_info['response_status'] = resp.status_code
            try:
                data = resp.json() if resp.content else {"status": "deleted"}
                debug_info['response_json'] = data
            except ValueError:
                data = {"status": "deleted"}
                debug_info['response_json'] = data

            if resp.status_code not in [200, 204]:
                raise Exception(f"Failed to delete BDOS profile '{name}': {data}")

            result['changed'] = True
            result['response'] = data

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == "__main__":
    main()
