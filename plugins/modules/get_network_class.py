# plugins/modules/get_network_class.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

documentation = r'''
---
module: get_network_class
short_description: Get the mapping of network classes and groups from a DefensePro device
options:
  provider:
    type: dict
    required: true
  dp_ip:
    type: str
    required: true
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        filter_class_name=dict(type='str', required=False, default=None)
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'], log_level=log_level, logger=logger)
        filter_class_name = module.params.get('filter_class_name')
        if filter_class_name:
            url = f"https://{provider['cc_ip']}/mgmt/v2/devices/{module.params['dp_ip']}/config/itemlist/rsBWMNetworkTable/{filter_class_name}"
        else:
            url = f"https://{provider['cc_ip']}/mgmt/v2/devices/{module.params['dp_ip']}/config/itemlist/rsBWMNetworkTable"
        debug_info = {
            'method': 'GET',
            'url': url,
            'body': None
        }
        logger.info(f"Getting network class info for device {module.params['dp_ip']} on cc_ip {provider['cc_ip']}")
        logger.debug(f"Request: {debug_info}")
        resp = cc._get(url)
        logger.debug(f"Response status: {resp.status_code}")
        try:
            data = resp.json()
            logger.debug(f"Response JSON: {data}")
        except ValueError:
            logger.error(f"Invalid JSON response: {resp.text}")
            raise Exception(f"Invalid JSON response: {resp.text}")
        result['response'] = data
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
