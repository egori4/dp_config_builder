from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: delete_http_profile
short_description: Delete an HTTP profile from Radware device
description:
  - Deletes an HTTP profile on Radware DefensePro via Radware CC API.
options:
  provider:
    description:
      - Connection details to Radware CC
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
    description:
      - Device IP where the profile exists
    type: str
    required: true
  http_profile_name:
    description:
      - Name of the HTTP profile to delete
    type: str
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Delete HTTP profile
  delete_http_profile:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    http_profile_name: "HTTP_Profile1"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        http_profile_name=dict(type='str', required=True),
    )

    result = dict(changed=False, response={})
    debug_info = {}

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    profile_name = module.params['http_profile_name']

    # Setup logger
    log_level = provider.get("log_level", "disabled")
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(
            provider['cc_ip'],
            provider['username'],
            provider['password'],
            log_level=log_level,
            logger=logger,
        )

        path = f"/mgmt/device/byip/{dp_ip}/config/rsHTTPProfileTable/{profile_name}"
        url = f"https://{provider['cc_ip']}{path}"

        debug_info['request'] = {"method": "DELETE", "url": url}
        logger.info(f"Deleting HTTP profile '{profile_name}' on device {dp_ip}")

        if not module.check_mode:
            resp = cc._delete(url)
            debug_info['response_status'] = resp.status_code

            try:
                data = resp.json() if resp.content else {"status": "deleted"}
            except ValueError:
                data = {"raw_response": resp.text or "Profile deleted"}

            debug_info['response_json'] = data

            if resp.status_code not in [200, 204]:
                raise Exception(f"Failed to delete HTTP profile '{profile_name}': {data}")

            result.update(changed=True, response=data)

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
