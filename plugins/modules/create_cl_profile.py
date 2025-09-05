# plugins/modules/create_cl_profile.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

DOCUMENTATION = r'''
---
module: create_cl_profile
short_description: Attach an IDS Connection Limit Attack to a Connection Limit Profile
description:
  - Ensures an IDS Connection Limit Attack is attached to a Connection Limit Profile
    on Radware DefensePro via Radware CC API (idempotent).
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
  dp_ip:
    type: str
    required: true
  cl_profile_name:
    description: Name of the Connection Limit Profile
    type: str
    required: true
  protection_name:
    description: Name of the Attack being attached
    type: str
    required: true
  protection_id:
    description: Attack ID (optional)
    type: str
    required: false
  action:
    description: Human-readable action (drop/forward/report)
    type: str
    required: false
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Attach existing CL attack to profile
  create_cl_profile:
    provider:
      server: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    cl_profile_name: "Test"
    protection_name: "Test_1"
    action: drop
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
changed:
  description: Whether any change was made
  type: bool
'''

# Human-readable → numeric mapping
ACTION_MAP = {
    "drop": 10,
    "forward": 20,
    "report": 30,
}

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        cl_profile_name=dict(type='str', required=True),
        protection_name=dict(type='str', required=True),
        protection_id=dict(type='str', required=False),
        action=dict(type='str', required=False),
    )

    result = dict(changed=False, response={}, debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')

    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(
            provider['server'], provider['username'], provider['password'],
            log_level=log_level, logger=logger
        )

        path = f"/mgmt/device/byip/{module.params['dp_ip']}/config/rsIDSConnectionLimitProfileTable/{module.params['cl_profile_name']}/{module.params['protection_name']}"
        url = f"https://{provider['server']}{path}"

        # Build desired body
        body = {
            "rsIDSConnectionLimitProfileName": module.params['cl_profile_name'],
            "rsIDSConnectionLimitProfileAttackName": module.params['protection_name'],
        }
        if module.params.get('protection_id'):
            body["rsIDSConnectionLimitProfileAttackId"] = module.params['protection_id']
        if module.params.get('action'):
            mapped = ACTION_MAP.get(module.params['action'].lower())
            if mapped:
                body["rsIDSConnectionLimitProfileAction"] = mapped

        # Skip in check_mode
        if module.check_mode:
            module.exit_json(changed=True, debug_info={"would_send": body})

        # Step 1: Check if entry exists
        check_resp = cc._get(url)
        if check_resp.status_code == 200:
            current = check_resp.json()
            # Compare existing vs desired
            diff = {k: v for k, v in body.items() if str(current.get(k)) != str(v)}

            if diff:
                logger.info(f"Updating existing CL profile mapping {body}")
                resp = cc._put(url, json=body)
                try:
                    result['response'] = resp.json()
                except ValueError:
                    result['response'] = {"raw": resp.text}
                result['changed'] = True
                result['debug_info'] = {"method": "PUT", "url": url, "body": body, "diff": diff}
            else:
                # Already matches → no change
                result['changed'] = False
                result['response'] = current
                result['debug_info'] = {"method": "NONE", "url": url, "body": body}

        elif check_resp.status_code == 404:
            # Step 2: Create new
            logger.info(f"Creating new CL profile mapping {body}")
            resp = cc._post(url, json=body)
            try:
                result['response'] = resp.json()
            except ValueError:
                result['response'] = {"raw": resp.text}
            result['changed'] = True
            result['debug_info'] = {"method": "POST", "url": url, "body": body}

        else:
            raise Exception(f"Unexpected response while checking existence: {check_resp.status_code} {check_resp.text}")

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
