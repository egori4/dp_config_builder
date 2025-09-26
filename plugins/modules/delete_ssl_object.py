# plugins/modules/delete_ssl_object.py
"""
Unified Ansible module to delete one or multiple SSL objects
on Radware DefensePro devices.

Supports:
- Multiple SSL objects per device
- Check mode
- Optional verification step
- Graceful skip of non-existent objects
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger
import traceback

DOCUMENTATION = r'''
---
module: delete_ssl_object
short_description: Delete SSL objects on DefensePro
description:
  - Deletes one or more SSL objects on DefensePro devices via Radware CC API.
  - Optionally verifies deletion by checking the SSL object table.
  - Skips non-existent SSL objects gracefully without failing.
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
  ssl_objects:
    description:
      - List of SSL object names (strings) to delete
    type: list
    required: true
  verify:
    description:
      - Whether to verify deletion by querying the SSL object table
    type: bool
    required: false
    default: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Delete multiple SSL objects
  delete_ssl_object:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: radware
      log_level: debug
    dp_ip: 10.105.192.32
    ssl_objects:
      - server1
      - server2
    verify: true
'''

RETURN = r'''
response:
  description: API response per SSL object
  type: list
debug_info:
  description: Request and response debug details
  type: dict
'''

# -------------------------------
# Helpers
# -------------------------------
def build_api_path(dp_ip, ssl_object):
    """Construct API endpoint path for SSL object deletion."""
    return f"/mgmt/device/byip/{dp_ip}/config/rsProtectedSslObjTable/{ssl_object}/"

def verify_ssl_absence(cc, provider_ip, dp_ip, ssl_object):
    """Verify that an SSL object no longer exists in the table."""
    path = f"/mgmt/device/byip/{dp_ip}/config/rsProtectedSslObjTable"
    url = f"https://{provider_ip}{path}"
    resp = cc._get(url)
    try:
        data = resp.json()
    except ValueError:
        data = {"raw_text": resp.text}
    existing_objects = data.get("rsProtectedSslObjTable", [])
    return not any(p.get("rsProtectedSslObjName") == ssl_object for p in existing_objects), data

# -------------------------------
# Main Module Logic
# -------------------------------
def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        ssl_objects=dict(type='list', required=True),
        verify=dict(type='bool', required=False, default=True),
    )

    result = dict(changed=False, response=[], debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    ssl_objects = module.params['ssl_objects']
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

        for obj in ssl_objects:
            # Ensure obj is string
            if isinstance(obj, dict):
                obj = obj.get('name')

            path = build_api_path(dp_ip, obj)
            url = f"https://{provider['cc_ip']}{path}"
            result['debug_info'].setdefault('requests', []).append({"method": "DELETE", "url": url})
            logger.info(f"Deleting SSL object '{obj}' on {dp_ip}")
            logger.debug(f"METHOD: DELETE, URL is {url}")

            if module.check_mode:
                result['response'].append({"ssl_object": obj, "msg": "Check mode - not deleted"})
                continue

            try:
                resp = cc._delete(url)
                status_code = resp.status_code
                result['debug_info'].setdefault('responses', []).append({"ssl_object": obj, "status_code": status_code})
                data = resp.json() if resp.content else {"status": "deleted"}

                if status_code not in (200, 204):
                    data.setdefault('error', f"HTTP {status_code}")
                    result['response'].append({"ssl_object": obj, "response": data, "failed": True})
                    logger.warning(f"SSL object '{obj}' may not exist or deletion failed: {data}")
                    continue

                if verify:
                    verified, verify_data = verify_ssl_absence(cc, provider['cc_ip'], dp_ip, obj)
                    result['debug_info'].setdefault('verify', []).append({"ssl_object": obj, "verified": verified})
                    if not verified:
                        result['response'].append({
                            "ssl_object": obj,
                            "response": data,
                            "failed": True,
                            "msg": "SSL object still exists after deletion"
                        })
                        logger.error(f"SSL object '{obj}' still exists after deletion")
                        continue

                result['response'].append({"ssl_object": obj, "response": data})
                result['changed'] = True

            except Exception as ex:
                result['response'].append({
                    "ssl_object": obj,
                    "response": {"error": str(ex), "traceback": traceback.format_exc()},
                    "failed": True
                })
                logger.error(f"Exception deleting SSL object '{obj}': {ex}")

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=str(e), **result)

def main():
    run_module()

if __name__ == "__main__":
    main()
