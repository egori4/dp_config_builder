from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

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
      server:
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
      server: 155.1.1.6
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
        http_profile_name=dict(type='str', required=True)
    )

    result = dict(changed=False, response={})
    debug_info = {}

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']

    try:
        cc = RadwareCC(provider['server'], provider['username'], provider['password'])

        if not module.check_mode:
            path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsHTTPProfileTable/{module.params['http_profile_name']}"
            url = f"https://{provider['server']}{path}"

            debug_info = {
                "method": "DELETE",
                "url": url
            }

            resp = cc._delete(url)
            try:
                data = resp.json()
            except ValueError:
                data = {"raw_response": resp.text}

            result['response'] = data
            result['changed'] = True

    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
