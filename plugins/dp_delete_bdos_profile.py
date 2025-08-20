from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: dp_delete_bdos_profile
short_description: Delete a BDOS Flood profile on Radware DefensePro
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
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['server'], provider['username'], provider['password'], log_level=log_level, logger=logger)
        if not module.check_mode:
            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsNetFloodProfileTable/{module.params['name']}"
            url = f"https://{provider['server']}{path}"
            debug_info = {
                'method': 'DELETE',
                'url': url,
                'body': None
            }
            logger.info(f"Deleting BDOS Flood profile {module.params['name']} on device {module.params['dp_ip']}")
            resp = cc._delete(url)
            logger.debug(f"Response status: {resp.status_code}")

            try:
                data = resp.json()
                logger.debug(f"Response JSON: {data}")
            except ValueError:
                logger.error(f"Invalid JSON response: {resp.text}")
                raise Exception(f"Invalid JSON response: {resp.text}")

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
