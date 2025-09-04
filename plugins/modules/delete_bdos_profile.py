# plugins/modules/delete_bdos_profile.py
"""
Ansible module to delete BDOS Flood profiles on Radware DefensePro devices.

This module allows you to delete an existing BDOS Flood profile via the Radware CyberController API.
It requires connection parameters for the Radware CC, the target DefensePro IP, and the profile name.

Module Arguments:
  provider (dict): Connection details for Radware CC.
  dp_ip (str): Target DefensePro IP.
  name (str): BDOS profile name to delete.

Returns:
  response (dict): API response from Radware CC.
  changed (bool): Indicates if deletion was successful.
  debug_info (dict): Debug info including request/response details.

Supports check mode.
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: delete_bdos_profile
short_description: Delete BDOS Flood profile
description:
  - Deletes a BDOS Flood profile on Radware DefensePro via Radware CC API.
options:
  provider:
    description:
      - Dictionary with connection parameters.
    type: dict
    required: true
    suboptions:
      cc_ip:
        description: CC IP address
        type: str
        required: true
      username:
        type: str
        required: true
      password:
        type: str
        required: true
      log_level:
        description: Logging verbosity (disabled, info, debug)
        type: str
        required: false
        default: disabled
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
  delete_bdos_profile:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    name: "BDOS_Test"
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
# Helpers
# -------------------------------
def build_api_path(dp_ip, name):
    """Construct API endpoint path for BDOS profile deletion."""
    return f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{name}/"


# -------------------------------
# Main Module Logic
# -------------------------------
def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=True),
    )

    result = dict(changed=False, response={}, debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    name = module.params['name']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    debug_info = {}

    # Validate provider fields
    for key in ('cc_ip', 'username', 'password'):
        if key not in provider or not provider[key]:
            module.fail_json(msg=f"Missing required provider field: {key}", **result)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        path = build_api_path(dp_ip, name)
        url = f"https://{provider['cc_ip']}{path}"
        debug_info['request'] = {"method": "DELETE", "url": url}
        logger.info(f"Deleting BDOS Flood profile '{name}' on {dp_ip}")

        if module.check_mode:
            result['changed'] = True
            result['response'] = {"msg": "Check mode - no changes applied"}
        else:
            resp = cc._delete(url)
            debug_info['response_status'] = resp.status_code

            try:
                data = resp.json() if resp.content else {"status": "deleted"}
            except Exception as ex:
                data = {"status": "deleted", "error": str(ex)}

            debug_info['response_json'] = data

            if resp.status_code not in (200, 204):
                module.fail_json(
                    msg=f"Failed to delete BDOS profile '{name}': {data}",
                    debug_info=debug_info,
                    **result
                )

            result['changed'] = True
            result['response'] = data

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)


# -------------------------------
# Entrypoint
# -------------------------------
def main():
    run_module()


if __name__ == "__main__":
    main()
