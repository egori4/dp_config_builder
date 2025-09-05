# plugins/modules/manage_bdos_delete.py
"""
Unified Ansible module to delete one or multiple BDOS Flood profiles
on Radware DefensePro devices.

This module handles deletion of BDOS Flood profiles via the Radware
CyberController API, supporting multiple profiles per device and
check mode.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: manage_bdos_delete
short_description: Delete BDOS Flood profiles on DefensePro
description:
  - Deletes one or more BDOS Flood profiles on DefensePro devices via Radware CC API.
options:
  provider:
    description:
      - Connection details for Radware CC
    type: dict
    required: true
    suboptions:
      cc_ip:
        description: Radware CC IP
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
  bdos_profiles:
    description:
      - List of BDOS Flood profile names to delete
    type: list
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Delete multiple BDOS Flood profiles
  manage_bdos_delete:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
      log_level: debug
    dp_ip: 155.1.1.7
    bdos_profiles:
      - BDOS_Test_1
      - BDOS_Test_2
'''

RETURN = r'''
response:
  description: API response per profile
  type: dict
debug_info:
  description: Request and response debug details
  type: dict
'''

# -------------------------------
# Helpers
# -------------------------------
def build_api_path(dp_ip, profile_name):
    """Construct API endpoint path for BDOS profile deletion."""
    return f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}/"

# -------------------------------
# Main Module Logic
# -------------------------------
def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        bdos_profiles=dict(type='list', required=True),
    )

    result = dict(changed=False, response={}, debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    bdos_profiles = module.params['bdos_profiles']
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

        profile_responses = []

        for profile_name in bdos_profiles:
            path = build_api_path(dp_ip, profile_name)
            url = f"https://{provider['cc_ip']}{path}"
            debug_info.setdefault('requests', []).append({"method": "DELETE", "url": url})
            logger.info(f"Deleting BDOS profile '{profile_name}' on {dp_ip}")

            if module.check_mode:
                profile_responses.append({"profile": profile_name, "msg": "Check mode - not deleted"})
                continue

            try:
                resp = cc._delete(url)
                debug_info.setdefault('responses', []).append({"profile": profile_name, "status_code": resp.status_code})
                try:
                    data = resp.json() if resp.content else {"status": "deleted"}
                except Exception as ex:
                    data = {"status": "deleted", "error": str(ex)}

                if resp.status_code not in (200, 204):
                    # Include API error but continue with other profiles
                    data.setdefault('error', f"HTTP {resp.status_code}")
                    profile_responses.append({"profile": profile_name, "response": data, "failed": True})
                    logger.error(f"Failed to delete BDOS profile '{profile_name}': {data}")
                else:
                    profile_responses.append({"profile": profile_name, "response": data})
                    result['changed'] = True

            except Exception as ex:
                profile_responses.append({"profile": profile_name, "response": {"error": str(ex)}, "failed": True})
                logger.error(f"Exception deleting BDOS profile '{profile_name}': {ex}")

        result['response'] = profile_responses
        result['debug_info'] = debug_info

        # Fail module if all profiles failed
        if all(p.get('failed') for p in profile_responses):
            module.fail_json(msg="All BDOS profile deletions failed", **result)

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=str(e), **result)

# -------------------------------
# Entrypoint
# -------------------------------
def main():
    run_module()


if __name__ == "__main__":
    main()
