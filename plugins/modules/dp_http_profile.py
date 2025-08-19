# plugins/modules/dp_http_profile.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

DOCUMENTATION = r'''
---
module: dp_http_profile
short_description: Create or manage HTTP/S flood profiles on Radware DefensePro
description:
  - Creates or updates an HTTP/S flood profile on DefensePro via Radware CC API.
options:
  provider:
    description:
      - Dictionary with connection parameters.
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
      verify_ssl:
        type: bool
        default: false
  device_ip:
    type: str
    required: true
  profile_name:
    type: str
    required: true
  profile:
    description:
      - Dictionary of HTTP/S flood profile settings (keys must match API payload fields).
    type: dict
    required: true
'''

EXAMPLES = r'''
- name: Create HTTP flood profile
  dp_http_profile:
    provider: "{{ cc }}"
    device_ip: 10.105.192.33
    profile_name: "HTTPS_Demo1"
    profile:
      rsHttpsFloodProfileName: "HTTPS_Demo1"
      rsHttpsFloodProfileAction: "1"
      rsHttpsFloodProfileRateLimit: "100"
      rsHttpsFloodProfileSelectiveChallenge: "2"
      rsHttpsFloodProfileCollectiveChallenge: "2"
      rsHttpsFloodProfileChallengeMethod: "2"
      rsHttpsFloodProfileRateLimitStatus: "1"
      rsHttpsFloodProfileFullSessionDecryption: "2"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        device_ip=dict(type='str', required=True),
        profile_name=dict(type='str', required=True),
        profile=dict(type='dict', required=True)
    )

    result = dict(changed=False, response={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    device_ip = module.params['device_ip']
    profile_name = module.params['profile_name']
    profile_payload = module.params['profile']

    try:
        cc = RadwareCC(
            provider['server'],
            provider['username'],
            provider['password'],
            verify_ssl=provider.get('verify_ssl', False)
        )
        if not module.check_mode:
            resp = cc.create_http_profile(device_ip, profile_name, profile_payload)
            result['response'] = resp
            result['changed'] = True
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
