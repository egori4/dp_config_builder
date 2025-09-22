# plugins/modules/delete_dns_profile.py
"""
Unified Ansible module to delete one or multiple DNS Protection profiles
on Radware DefensePro devices.

Handles deletion via the Radware CyberController API,
supports multiple profiles per device, check mode, and skips non-existent profiles without failing.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: delete_dns_profile
short_description: Delete DNS Protection profiles on DefensePro
description:
  - Deletes one or more DNS Protection profiles on DefensePro devices via Radware CC API.
  - Gracefully skips profiles that do not exist.
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
  dns_profiles:
    description:
      - List of DNS Protection profile names to delete
    type: list
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Delete multiple DNS Protection profiles
  delete_dns_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
      log_level: debug
    dp_ip: 10.105.192.33
    dns_profiles:
      - name: DNS_Profile_1
      - name: DNS_Profile_2
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
    """Construct API endpoint path for DNS profile deletion."""
    return f"/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name['name']}/"

# -------------------------------
# Main Module Logic
# -------------------------------
def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        dns_profiles=dict(type='list', required=True),
    )

    result = dict(changed=False, response=[], debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    dns_profiles = module.params['dns_profiles']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    # Validate provider fields
    for key in ('cc_ip', 'username', 'password'):
        if key not in provider or not provider[key]:
            module.fail_json(msg=f"Missing required provider field: {key}", **result)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        for profile_name in dns_profiles:
            path = build_api_path(dp_ip, profile_name)
            url = f"https://{provider['cc_ip']}{path}"
            result['debug_info'].setdefault('requests', []).append({"method": "DELETE", "url": url})
            logger.info(f"Deleting DNS profile '{profile_name['name']}' on {dp_ip}")
            logger.debug(f"DELETE URL: {url}")

            if module.check_mode:
                result['response'].append({"profile": profile_name, "msg": "Check mode - not deleted"})
                continue

            try:
                resp = cc._delete(url)
                status_code = resp.status_code
                result['debug_info'].setdefault('responses', []).append({"profile": profile_name, "status_code": status_code})
                logger.debug(f"Response status: {status_code}")

                data = resp.json() if resp.content else {"status": "deleted"}
                logger.debug(f"Response JSON: {data}")

                if status_code not in (200, 204):
                    data.setdefault('error', f"HTTP {status_code}")
                    result['response'].append({"profile": profile_name, "response": data, "failed": True})
                    logger.error(f"Failed to delete DNS profile '{profile_name['name']}': {data}")
                else:
                    result['response'].append({"profile": profile_name, "response": data})
                    result['changed'] = True

            except Exception as ex:
                result['response'].append({"profile": profile_name, "response": {"error": str(ex)}, "failed": True})
                logger.error(f"Exception deleting DNS profile '{profile_name['name']}': {ex}")

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
