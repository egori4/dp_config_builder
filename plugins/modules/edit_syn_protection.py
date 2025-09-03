# plugins/modules/edit_syn_protection.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: edit_syn_protection
short_description: Edit a SYN Protection on DefensePro device
description:
  - Edits an existing SYN protection on Radware DefensePro via Radware CC API.
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
  protection_id:
    description: Protection ID of the SYN protection
    type: str
    required: true
  name:
    description: Friendly name for the SYN protection
    type: str
    required: true
  app_port_group:
    description: Destination application port group (e.g., http, https)
    type: str
    required: true
  activation_threshold:
    description: Attack activation threshold
    type: int
    required: true
  termination_threshold:
    description: Attack termination threshold
    type: int
    required: true
  packet_report:
    description: Enable or disable packet reporting
    type: str
    required: true
    choices: [enable, disable]
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Edit SYN protection
  edit_syn_protection:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    protection_id: "500013"
    name: "TEST"
    app_port_group: "http"
    activation_threshold: 2500
    termination_threshold: 2000
    packet_report: enable
'''

RETURN = r'''
response:
  description: API response
  type: dict
debug_info:
  description: Request/response debug details
  type: dict
'''


def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        protection_id=dict(type='str', required=True),
        name=dict(type='str', required=True),
        app_port_group=dict(type='str', required=True),
        activation_threshold=dict(type='int', required=True),
        termination_threshold=dict(type='int', required=True),
        packet_report=dict(type='str', required=True, choices=['enable', 'disable']),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    protection_id = module.params['protection_id']
    name = module.params['name']
    app_port_group = module.params['app_port_group']
    activation_threshold = module.params['activation_threshold']
    termination_threshold = module.params['termination_threshold']
    packet_report = module.params['packet_report']

    cc_ip = provider.get('cc_ip')
    username = provider.get('username')
    password = provider.get('password')
    verify_ssl = provider.get('verify_ssl', False)
    log_level = provider.get('log_level', 'disabled')

    logger = Logger(verbosity=log_level)
    debug_info = {}

    try:
        cc = RadwareCC(cc_ip, username, password,
                       verify_ssl=verify_ssl, log_level=log_level, logger=logger)

        url = f"https://{cc_ip}/mgmt/device/byip/{dp_ip}/config/rsIDSSYNAttackTable/{protection_id}"

        body = {
            "rsIDSSYNAttackName": name,
            "rsIDSSYNDestinationAppPortGroup": app_port_group,
            "rsIDSSYNAttackActivationThreshold": activation_threshold,
            "rsIDSSYNAttackTerminationThreshold": termination_threshold,
            "rsIDSSYNAttackPacketReport": 1 if packet_report == "enable" else 2,
        }

        debug_info = {'method': 'PUT', 'url': url, 'body': body}
        logger.info(f"Editing SYN protection {protection_id} on {dp_ip}")
        logger.debug(f"PUT Request: {debug_info}")

        if module.check_mode:
            module.exit_json(changed=True, response={"msg": "Check mode - no changes applied"}, debug_info=debug_info)

        resp = cc._put(url, json=body)
        try:
            data = resp.json()
        except ValueError:
            raise Exception(f"Invalid JSON response: {resp.text}")

        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to edit SYN protection: {data}")

        debug_info.update({'response_status': resp.status_code, 'response_json': data})
        module.exit_json(changed=True, response=data, debug_info=debug_info)

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info)


def main():
    run_module()


if __name__ == '__main__':
    main()
