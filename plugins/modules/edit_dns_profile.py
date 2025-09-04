# plugins/modules/edit_dns_profile.py
"""
Ansible module to edit/update a DNS Protection profile on DefensePro via Radware CyberController API.

This module allows you to update an existing DNS Protection profile on Radware DefensePro devices
using the Radware CyberController API. It requires connection parameters for the Radware CyberController,
the target DefensePro IP, and the DNS profile details to update.

Functions:
  run_module():
    Main logic for the module. Handles argument parsing, logging, API request construction,
    and response handling. Supports check mode.

  main():
    Entrypoint for the module execution.

Module Arguments:
  provider (dict): Connection parameters for Radware CyberController.
    - cc_ip (str): CyberController IP address.
    - username (str): Username for authentication.
    - password (str): Password for authentication.
    - log_level (str, optional): Logging verbosity (default: 'disabled').
  dp_ip (str): Target DefensePro device IP address.
  name (str): DNS profile name to edit.
  params (dict): DNS profile parameters to update in user-friendly format.

Returns:
  response (dict): API response from Radware CyberController.
  changed (bool): Indicates if any change was made.
  debug_info (dict): Debug information including request and response details.
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: edit_dns_profile
short_description: Edit an existing DNS Protection profile on DefensePro
options:
  provider:
    description:
      - Dictionary with connection parameters.
    type: dict
    required: true
    suboptions:
      cc_ip:
        description: CyberController IP address
        type: str
        required: true
      username:
        description: Username for authentication
        type: str
        required: true
      password:
        description: Password for authentication
        type: str
        required: true
      log_level:
        description: Logging verbosity
        type: str
        required: false
        default: "disabled"
  dp_ip:
    description: Target DefensePro device IP
    type: str
    required: true
  name:
    description: DNS profile name to edit
    type: str
    required: true
  params:
    description: DNS profile parameters to update
    type: dict
    required: true
'''

EXAMPLES = r'''
- name: Edit DNS Protection profile
  edit_dns_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
    dp_ip: 10.105.192.33
    name: "DNS_Profile_1"
    params:
      DNS Expected Qps: "5000"
      DNS Max Allow Qps: "5500"
      DNS Footprint Strictness: "high"
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
debug_info:
  description: Internal debug information including request and response
  type: dict
'''

# Mapping user-friendly keys → API keys
FIELD_MAP = {
    "DNS Expected Qps": "rsDnsProtProfileExpectedQps",
    "DNS Action": "rsDnsProtProfileAction",
    "DNS Max Allow Qps": "rsDnsProtProfileMaxAllowQps",
    "DNS Manual Trigger Status": "rsDnsProtProfileManualTriggerStatus",
    "DNS Footprint Strictness": "rsDnsProtProfileFootprintStrictness",
    "DNS Packet Report Status": "rsDnsProtProfilePacketReportStatus",
    "DNS Learning Suppression Threshold": "rsDnsProtProfileLearningSuppressionThreshold",
}

# Numeric mapping for user-friendly values
NUMERIC_MAPPING = {
    "DNS Action": {"report": 0, "block & report": 1},
    "DNS Manual Trigger Status": {"enable": 1, "disable": 2},
    "DNS Footprint Strictness": {"low": 0, "medium": 1, "high": 2},
    "DNS Packet Report Status": {"enable": 1, "disable": 2},
}

def translate_params(params):
    """Convert user-friendly keys and values to Radware API format."""
    translated = {}
    for key, val in params.items():
        api_key = FIELD_MAP.get(key, key)
        if key in NUMERIC_MAPPING:
            val_lower = str(val).lower()
            if val_lower not in NUMERIC_MAPPING[key]:
                raise ValueError(f"Invalid value '{val}' for {key}")
            translated[api_key] = NUMERIC_MAPPING[key][val_lower]
        else:
            translated[api_key] = int(val) if str(val).isdigit() else val
    return translated

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=True),
        params=dict(type='dict', required=True)
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    profile_name = module.params['name']
    profile_params = module.params['params']
    log_level = provider.get('log_level', 'disabled')

    result = dict(changed=False, response={}, debug_info={})
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(
            provider['cc_ip'],
            provider['username'],
            provider['password'],
            log_level=log_level,
            logger=logger
        )

        if module.check_mode:
            module.exit_json(**result)

        path = f"/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}"
        body = translate_params(profile_params)

        url = f"https://{provider['cc_ip']}{path}"
        result['debug_info'] = {'method': 'PUT', 'url': url, 'body': body}

        logger.info(f"Editing DNS Protection profile '{profile_name}' on device {dp_ip}")
        logger.debug(f"Request payload: {body}")

        resp = cc._put(url, json=body)
        logger.debug(f"Response status: {resp.status_code}")

        try:
            data = resp.json()
        except ValueError:
            logger.error(f"Invalid JSON response: {resp.text}")
            raise Exception(f"Invalid JSON response: {resp.text}")

        result['response'] = data
        result['changed'] = True
        result['debug_info'].update({'response_status': resp.status_code, 'response_json': data})

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
