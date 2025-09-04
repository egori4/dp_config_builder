# plugins/modules/edit_bdos_profile.py
"""
Ansible module to edit existing BDOS Flood profiles on DefensePro devices via Radware CyberController API.

This module allows you to modify an existing BDOS Flood profile on Radware DefensePro devices
using the Radware CyberController API. It requires connection parameters for the Radware CyberController,
the target DefensePro IP, and the BDOS Flood profile parameters to modify.

Classes:
  None

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
  name (str): Name of the existing BDOS Flood profile.
  params (dict): Dictionary of BDOS Flood profile attributes to update.

Returns:
  response (dict): API response from Radware CyberController.
  changed (bool): Indicates if any change was made.
  debug_info (dict): Debug information including request and response details.

Exceptions:
  Raises Exception if API response is invalid or if any error occurs during execution.

References:
  - Radware CyberController API documentation for BDOS profile management.
  - AnsibleModule documentation: https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html
  - RadwareCC utility: ansible.module_utils.radware_cc
  - Logger utility: ansible.module_utils.logger

Note:
  The module supports check mode and provides detailed logging if log_level is set.
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: edit_bdos_profile
short_description: Edit existing BDOS Flood profiles
description:
  - Modifies an existing BDOS Flood profile on Radware DefensePro via Radware CC API.
options:
  provider:
    description:
      - Dictionary with connection parameters.
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
      log_level:
        type: str
        required: false
        default: disabled
  dp_ip:
    type: str
    required: true
  name:
    type: str
    required: true
  params:
    type: dict
    required: true
'''

EXAMPLES = r'''
- name: Edit a BDOS Flood profile
  edit_bdos_profile:
    provider:
      cc_ip: 10.105.193.3
      username: radware
      password: mypass
      log_level: debug
    dp_ip: 10.105.192.32
    name: BDOS_Profile_10
    params:
      TCP Status: active
      UDP Status: inactive
      ICMP Status: active
      Bandwidth In: 50000
      Bandwidth Out: 50000
      Action: block & report
'''

RETURN = r'''
response:
  description: API response from Radware CC
  type: dict
debug_info:
  description: Debug information about request/response
  type: dict
'''

# -------------------------------
# Field Mappings & Numeric Conversions
# -------------------------------
FIELD_MAP = {
    "TCP Status": "rsNetFloodProfileTcpStatus",
    "UDP Status": "rsNetFloodProfileUdpStatus",
    "ICMP Status": "rsNetFloodProfileIcmpStatus",
    "TCP SYN/ACK Status": "rsNetFloodProfileTcpSynAckStatus",
    "TCP Frag Status": "rsNetFloodProfileTcpFragStatus",
    "Bandwidth In": "rsNetFloodProfileBandwidthIn",
    "Bandwidth Out": "rsNetFloodProfileBandwidthOut",
    "Transparent Optimization": "rsNetFloodProfileTransparentOptimization",
    "Action": "rsNetFloodProfileAction",
    "Burst Enabled": "rsNetFloodProfileBurstEnabled",
    "Learning Suppression Threshold": "rsNetFloodProfileLearningSuppressionThreshold",
    "Footprint Strictness": "rsNetFloodProfileFootprintStrictness",
    "Rate Limit": "rsNetFloodProfileRateLimit",
    "Packet Report Status": "rsNetFloodProfilePacketReportStatus",
    "Packet Trace Status": "rsNetFloodProfilePacketTraceStatus",
}

NUMERIC_MAPPING = {
    "TCP Status": {"active": 1, "inactive": 2},
    "UDP Status": {"active": 1, "inactive": 2},
    "ICMP Status": {"active": 1, "inactive": 2},
    "TCP SYN/ACK Status": {"active": 1, "inactive": 2},
    "TCP Frag Status": {"active": 1, "inactive": 2},
    "Transparent Optimization": {"yes": 1, "no": 2},
    "Footprint Strictness": {"low": 0, "medium": 1, "high": 2},
    "Packet Report Status": {"enable": 1, "disable": 2},
    "Packet Trace Status": {"enable": 1, "disable": 2},
    "Action": {"report only": 0, "block & report": 1},
    "Burst Enabled": {"enable": 1, "disable": 2},
}

FIELD_RANGES = {
    "Learning Suppression Threshold": (0, 50),
}

# -------------------------------
# Helpers
# -------------------------------
def translate_params(params):
    translated = {}
    for k, v in params.items():
        api_key = FIELD_MAP.get(k, k)
        mapping = NUMERIC_MAPPING.get(k)
        if mapping:
            val = str(v).lower()
            if val not in mapping:
                raise ValueError(f"Invalid value '{v}' for '{k}'. Allowed: {list(mapping.keys())}")
            translated[api_key] = mapping[val]
        elif k in FIELD_RANGES:
            min_val, max_val = FIELD_RANGES[k]
            num_val = int(v)
            if not (min_val <= num_val <= max_val):
                raise ValueError(f"Field '{k}' must be in range [{min_val}..{max_val}]")
            translated[api_key] = num_val
        else:
            translated[api_key] = v
    return translated

def build_api_path(dp_ip, name):
    return f"/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{name}"

# -------------------------------
# Main Logic
# -------------------------------
def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        name=dict(type='str', required=True),
        params=dict(type='dict', required=True),
    )

    result = dict(changed=False, response={}, debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    name = module.params['name']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    debug_info = {}

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                       log_level=log_level, logger=logger)
        path = build_api_path(dp_ip, name)
        url = f"https://{provider['cc_ip']}{path}"
        body = {"rsNetFloodProfileName": name}
        body.update(translate_params(module.params['params']))

        debug_info['request'] = {"method": "PUT", "url": url, "body": body}
        logger.info(f"Editing BDOS Flood profile '{name}' on {dp_ip}")
        logger.debug(f"Request: {debug_info}")

        if module.check_mode:
            result['changed'] = True
            result['response'] = {"msg": "Check mode - no changes applied"}
        else:
            resp = cc._put(url, json=body)
            debug_info['response_status'] = resp.status_code
            try:
                data = resp.json()
                debug_info['response_json'] = data
            except ValueError:
                raise Exception(f"Invalid JSON response: {resp.text}")

            if resp.status_code not in (200, 201):
                raise Exception(f"Failed to edit BDOS profile: {data}")

            result['changed'] = True
            result['response'] = data

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == "__main__":
    main()
