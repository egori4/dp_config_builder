<<<<<<< HEAD
# plugins/modules/dp_unlock.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: dp_unlock
short_description: Unlock a DefensePro device via Radware CC
options:
  provider:
    description: Connection details for Radware CC
    required: true
    type: dict
    suboptions:
      cc_ip:
        type: str
        required: true
      username:
        type: str
        required: true
      password:
        type: str
        required: true
      verify_ssl:
        type: bool
        required: false
        default: false
  dp_ip:
    description: DefensePro device IP to unlock
    required: true
    type: str
'''

EXAMPLES = r'''
- name: Unlock device
  dp_unlock:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
      verify_ssl: false
    dp_ip: 10.105.192.32
'''

RETURN = r'''
status:
  description: API status response
  type: dict
  returned: always
changed:
  description: Whether configuration state changed
  type: bool
  returned: always
'''

def run_module():
    args_spec = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
    )

    module = AnsibleModule(argument_spec=args_spec, supports_check_mode=False)

    provider = module.params['provider'] or {}
    dp_ip = module.params['dp_ip']

    cc_ip = provider.get('cc_ip')
    user = provider.get('username')
    password = provider.get('password')
    verify_ssl = provider.get('verify_ssl', False)

    if not all([cc_ip, user, password]):
        module.fail_json(msg="provider.cc_ip, provider.username and provider.password are required")

    
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    debug_info = {}
    try:
      cc = RadwareCC(cc_ip, user, password, verify_ssl=verify_ssl, log_level=log_level, logger=logger)
      url = f"https://{cc_ip}/mgmt/system/config/tree/device/byip/{dp_ip}/unlock"
      debug_info = {
        'method': 'POST',
        'url': url,
        'body': None
      }
      logger.info(f"Unlocking device {dp_ip} on cc_ip {cc_ip}")
      logger.debug(f"Request: {debug_info}")
      resp = cc._post(url)
      logger.debug(f"Response status: {resp.status_code}")
      data = resp.json()
      logger.debug(f"Response JSON: {data}")
      if isinstance(data, dict) and data.get("status") == "ok":
        debug_info['response_status'] = resp.status_code
        debug_info['response_json'] = data
        module.exit_json(changed=True, status=data, debug_info=debug_info)
      else:
        logger.error(f"Unexpected unlock response: {data}")
        module.fail_json(msg=f"Unexpected unlock response: {data}", status=data, debug_info=debug_info)
    except Exception as e:
      logger.error(f"Exception: {str(e)}")
      module.fail_json(msg=str(e), debug_info=debug_info)

def main():
    run_module()

if __name__ == '__main__':
    main()
=======
# plugins/modules/dp_unlock.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: dp_unlock
short_description: Unlock a DefensePro device via Radware CC
options:
  provider:
    description: Connection details for Radware CC
    required: true
    type: dict
    suboptions:
      cc_ip:
        type: str
        required: true
      username:
        type: str
        required: true
      password:
        type: str
        required: true
      verify_ssl:
        type: bool
        required: false
        default: false
  dp_ip:
    description: DefensePro device IP to unlock
    required: true
    type: str
'''

EXAMPLES = r'''
- name: Unlock device
  dp_unlock:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
      verify_ssl: false
    dp_ip: 10.105.192.32
'''

RETURN = r'''
status:
  description: API status response
  type: dict
  returned: always
changed:
  description: Whether configuration state changed
  type: bool
  returned: always
'''

def run_module():
    args_spec = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
    )

    module = AnsibleModule(argument_spec=args_spec, supports_check_mode=False)

    provider = module.params['provider'] or {}
    dp_ip = module.params['dp_ip']

    cc_ip = provider.get('cc_ip')
    user = provider.get('username')
    password = provider.get('password')
    verify_ssl = provider.get('verify_ssl', False)

    if not all([cc_ip, user, password]):
        module.fail_json(msg="provider.cc_ip, provider.username and provider.password are required")

    
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    debug_info = {}
    try:
      cc = RadwareCC(cc_ip, user, password, verify_ssl=verify_ssl, log_level=log_level, logger=logger)
      url = f"https://{cc_ip}/mgmt/system/config/tree/device/byip/{dp_ip}/unlock"
      debug_info = {
        'method': 'POST',
        'url': url,
        'body': None
      }
      logger.info(f"Unlocking device {dp_ip} on cc_ip {cc_ip}")
      logger.debug(f"Request: {debug_info}")
      resp = cc._post(url)
      logger.debug(f"Response status: {resp.status_code}")
      data = resp.json()
      logger.debug(f"Response JSON: {data}")
      if isinstance(data, dict) and data.get("status") == "ok":
        debug_info['response_status'] = resp.status_code
        debug_info['response_json'] = data
        module.exit_json(changed=True, status=data, debug_info=debug_info)
      else:
        logger.error(f"Unexpected unlock response: {data}")
        module.fail_json(msg=f"Unexpected unlock response: {data}", status=data, debug_info=debug_info)
    except Exception as e:
      logger.error(f"Exception: {str(e)}")
      module.fail_json(msg=str(e), debug_info=debug_info)

def main():
    run_module()

if __name__ == '__main__':
    main()
>>>>>>> upstream/main
