#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: delete_https_profile
short_description: Delete an HTTPS Flood profile on Radware DefensePro via CC API
description:
  - Deletes an existing HTTPS Flood profile from a DefensePro device using Radware CC API.
options:
  provider:
    description:
      - Dictionary with CC connection parameters
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
  dp_ip:
    description: DefensePro device IP managed by CC
    type: str
    required: true
  name:
    description: Name of the HTTPS Flood profile to delete
    type: str
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Delete HTTPS Flood profile
  delete_https_profile:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    name: "HTTPS_Profile_1"
'''

RETURN = r'''
response:
  description: API response from CC
  type: dict
changed:
  description: True if a profile was deleted
  type: bool
'''

def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            provider=dict(type='dict', required=True),
            dp_ip=dict(type='str', required=True),
            name=dict(type='str', required=True),
        ),
        supports_check_mode=True
    )

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    profile_name = module.params['name']

    result = {"changed": False, "response": {}}
    debug_info = {}

    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)

        # Build DELETE URL for HTTPS Flood profile
        url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsHttpsFloodProfileTable/{profile_name}"
        debug_info.update({"method": "DELETE", "url": url})

        logger.info(f"Deleting HTTPS Flood profile '{profile_name}' on {dp_ip}")
        logger.debug(f"Request: {debug_info}")

        if module.check_mode:
            module.exit_json(changed=True, msg="Check mode: profile would be deleted", debug_info=debug_info)

        resp = cc._delete(url)
        debug_info["response_status"] = resp.status_code

        # Parse response
        if resp.headers.get("Content-Type") == "application/json":
            data = resp.json()
        else:
            data = {"raw": resp.text}

        # Determine if deletion was successful
        if resp.status_code in [200, 204]:
            result["changed"] = True
        elif resp.status_code == 404:
            result["changed"] = False
            data = {"msg": f"Profile '{profile_name}' not found"}
        else:
            module.fail_json(msg=f"Failed to delete profile: HTTP {resp.status_code}", debug_info=debug_info)

        result["response"] = data
        debug_info["response_json"] = data

    except Exception as e:
        logger.error(f"Exception: {e}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result["debug_info"] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == "__main__":
    main()
