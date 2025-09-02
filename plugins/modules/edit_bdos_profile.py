# plugins/modules/dp_bdos_edit_profile.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: dp_bdos_edit_profile
short_description: Edit DefensePro BDOS Flood profiles via Radware CC
description:
  - Updates existing BDOS Flood profiles on Radware DefensePro devices using Radware CC API (PUT method).
options:
  provider:
    description:
      - Dictionary with connection parameters for Radware CC.
    type: dict
    required: true
  dp_ip:
    description: DefensePro device IP address
    type: str
    required: true
  name:
    description: BDOS Flood profile name
    type: str
    required: true
  params:
    description:
      - Dictionary of BDOS Flood profile attributes and values
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Edit BDOS Flood profile
  dp_bdos_edit_profile:
    provider: "{{ provider }}"
    dp_ip: 155.1.1.7
    name: "BDOS_Test"
    params:
      TCP Status: "inactive"
      Action: "report"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
debug_info:
  description: Request and response debug details
  type: dict
'''

# -------------------------------
# Import mappings from create module for consistency
# -------------------------------
from ansible_collections.your_namespace.your_collection.plugins.modules.dp_bdos_profile import (
    FIELD_MAP, NUMERIC_MAPPING, translate_params
)

# -------------------------------
# Main Logic
# -------------------------------
def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=True),
        params=dict(type='dict', required=True),
    )

    result = dict(changed=False, response={}, debug_info={})

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')

    logger = Logger(verbosity=log_level)
    debug_info = {}

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        if not module.check_mode:
            path = (
                f"/mgmt/device/byip/{module.params['dp_ip']}"
                f"/config/rsNetFloodProfileTable/{module.params['name']}"
            )
            body = {"rsNetFloodProfileName": module.params['name']}
            body.update(translate_params(module.params['params']))

            url = f"https://{provider['cc_ip']}{path}"
            debug_info['request'] = {"method": "PUT", "url": url, "body": body}
            logger.info(f"Editing BDOS Flood profile '{module.params['name']}' on {module.params['dp_ip']}")

            # Prefer public request method
            resp = cc.put(url, json=body) if hasattr(cc, "put") else cc._put(url, json=body)

            debug_info['response_status'] = resp.status_code
            try:
                data = resp.json()
                debug_info['response_json'] = data
            except ValueError:
                raise Exception(f"Invalid JSON response: {resp.text}")

            if resp.status_code not in (200, 201):
                raise Exception(f"Failed to edit BDOS profile: {data}")

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
