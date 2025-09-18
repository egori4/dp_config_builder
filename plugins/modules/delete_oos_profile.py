# plugins/modules/delete_oos_profile.py
"""
Unified Ansible module to delete one or multiple OOS/Stateful profiles
on Radware DefensePro devices.

Supports:
- Multiple profiles per device
- Check mode
- Optional verification step
- Graceful skip of non-existent profiles
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger
import traceback

DOCUMENTATION = r'''
---
module: delete_oos_profile
short_description: Delete OOS/Stateful profiles on DefensePro
description:
  - Deletes one or more OOS/Stateful profiles on DefensePro devices via Radware CC API.
  - Optionally verifies deletion by checking the profile table.
  - Skips non-existent profiles gracefully without failing.
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
  oos_profiles:
    description:
      - List of OOS/Stateful profile names to delete
    type: list
    required: true
  verify:
    description:
      - Whether to verify deletion by querying the profile table
    type: bool
    required: false
    default: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Delete multiple OOS profiles
  delete_oos_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: radware
      log_level: debug
    dp_ip: 10.105.192.32
    oos_profiles:
      - Test1
      - Test2
    verify: true
'''

RETURN = r'''
response:
  description: API response per profile
  type: list
debug_info:
  description: Request and response debug details
  type: dict
'''

# -------------------------------
# Helpers
# -------------------------------
def build_api_path(dp_ip, profile_name):
    """Construct API endpoint path for OOS profile deletion."""
    return f"/mgmt/device/byip/{dp_ip}/config/rsStatefulProfileTable/{profile_name}/"

def verify_profile_absence(cc, provider_ip, dp_ip, profile_name):
    """Verify that a profile no longer exists in the table."""
    path = f"/mgmt/device/byip/{dp_ip}/config/rsStatefulProfileTable"
    url = f"https://{provider_ip}{path}"
    resp = cc._get(url)
    try:
        data = resp.json()
    except ValueError:
        data = {"raw_text": resp.text}
    existing_profiles = data.get("rsStatefulProfileTable", [])
    return not any(p.get("rsStatefulProfileName") == profile_name for p in existing_profiles), data

# -------------------------------
# Main Module Logic
# -------------------------------
def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        oos_profiles=dict(type='list', required=True),
        verify=dict(type='bool', required=False, default=True),
    )

    result = dict(changed=False, response=[], debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    oos_profiles = module.params['oos_profiles']
    verify = module.params['verify']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    # Validate provider fields
    for key in ('cc_ip', 'username', 'password'):
        if key not in provider or not provider[key]:
            module.fail_json(msg=f"Missing required provider field: {key}", **result)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        for profile_name in oos_profiles:
            path = build_api_path(dp_ip, profile_name)
            url = f"https://{provider['cc_ip']}{path}"
            result['debug_info'].setdefault('requests', []).append({"method": "DELETE", "url": url})
            logger.info(f"Deleting OOS profile '{profile_name}' on {dp_ip}")

            if module.check_mode:
                result['response'].append({"profile": profile_name, "msg": "Check mode - not deleted"})
                continue

            try:
                resp = cc._delete(url)
                status_code = resp.status_code
                result['debug_info'].setdefault('responses', []).append({"profile": profile_name, "status_code": status_code})

                data = resp.json() if resp.content else {"status": "deleted"}
                logger.debug(f"Response JSON: {data}")

                if status_code not in (200, 204):
                    # Non-existent or failed deletion → skip gracefully
                    data.setdefault('error', f"HTTP {status_code}")
                    result['response'].append({"profile": profile_name, "response": data, "failed": True})
                    logger.warning(f"Profile '{profile_name}' may not exist or deletion failed: {data}")
                    continue

                # Verification step
                if verify:
                    verified, verify_data = verify_profile_absence(cc, provider['cc_ip'], dp_ip, profile_name)
                    result['debug_info'].setdefault('verify', []).append({"profile": profile_name, "verified": verified})
                    if not verified:
                        result['response'].append({
                            "profile": profile_name,
                            "response": data,
                            "failed": True,
                            "msg": "Profile still exists after deletion"
                        })
                        logger.error(f"Profile '{profile_name}' still exists after deletion")
                        continue

                result['response'].append({"profile": profile_name, "response": data})
                result['changed'] = True

            except Exception as ex:
                result['response'].append({
                    "profile": profile_name,
                    "response": {"error": str(ex), "traceback": traceback.format_exc()},
                    "failed": True
                })
                logger.error(f"Exception deleting OOS profile '{profile_name}': {ex}")

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
