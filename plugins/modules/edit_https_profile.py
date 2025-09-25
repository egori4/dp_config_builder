#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

DOCUMENTATION = r'''
---
module: edit_https_profile
short_description: Edit an HTTPS Flood profile on Radware DefensePro
description:
  - Updates an existing HTTPS Flood profile on a DefensePro device using PUT via Radware CC API.
options:
  provider:
    description: CC connection parameters
    type: dict
    required: true
    suboptions:
      cc_ip: {type: str, required: true}
      username: {type: str, required: true}
      password: {type: str, required: true}
  dp_ip:
    description: DefensePro device IP
    type: str
    required: true
  name:
    description: Profile name to edit (must already exist)
    type: str
    required: true
  params:
    description: Dictionary of friendly parameters for the profile
    type: dict
    required: true
author:
  - "Your Name"
'''

EXAMPLES = r'''
- name: Edit HTTPS Flood profile
  edit_https_profile:
    provider:
      cc_ip: 155.1.1.6
      username: radware
      password: mypass
    dp_ip: 155.1.1.7
    name: "HTTPS_Demo1"
    params:
      action: "block_and_report"
      rate_limit: "100000"
      selective_challenge: "disable"
      collective_challenge: "enable"
      challenge_method: "javaScript"
      rate_limit_status: "enable"
      full_session_decryption: "disable"
'''

RETURN = r'''
response:
  description: API response from CC
  type: dict
changed:
  description: True if the profile was updated
  type: bool
'''

# Friendly → API enumerations
ENUM_MAPS = {
    "action": {"report_only": "0", "block_and_report": "1"},
    "https_authentication_on_suspect_sources": {"enable": "1", "disable": "2"},
    "https_authentication_on_all_sources": {"enable": "1", "disable": "2"},
    "challenge_method": {"redirect_302": "1", "javascript": "2"},
    "rate_limit_status": {"enable": "1", "disable": "2"},
    "packet_report": {"enable": "1", "disable": "2"},
    "full_session_decryption": {"enable": "1", "disable": "2"}
}

# Friendly field → API field
FIELD_MAP = {
    "action": "rsHttpsFloodProfileAction",
    "rate_limit": "rsHttpsFloodProfileRateLimit",
    "https_authentication_on_suspect_sources": "rsHttpsFloodProfileSelectiveChallenge",
    "https_authentication_on_all_sources": "rsHttpsFloodProfileCollectiveChallenge",
    "challenge_method": "rsHttpsFloodProfileChallengeMethod",
    "rate_limit_status": "rsHttpsFloodProfileRateLimitStatus",
    "packet_report": "rsHttpsFloodProfilePacketReporting",
    "full_session_decryption": "rsHttpsFloodProfileFullSessionDecryption"
}


def translate_params(params):
    """Translate friendly params into API format using FIELD_MAP and ENUM_MAPS."""
    translated = {}
    for k, v in params.items():
        api_key = FIELD_MAP.get(k, k)
        if k in ENUM_MAPS:
            translated[api_key] = ENUM_MAPS[k].get(str(v), str(v))
        else:
            translated[api_key] = str(v)
    return translated


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            provider=dict(type='dict', required=True),
            dp_ip=dict(type='str', required=True),
            name=dict(type='str', required=True),
            params=dict(type='dict', required=True),
        ),
        supports_check_mode=True
    )

    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    profile_name = module.params['name']
    params = translate_params(module.params['params'])

    result = {"changed": False, "response": {}}
    debug_info = {}

    logger = Logger(verbosity=provider.get('log_level', 'disabled'))

    cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'],
                   log_level=provider.get('log_level', 'disabled'), logger=logger)

    url = f"https://{provider['cc_ip']}/mgmt/device/byip/{dp_ip}/config/rsHttpsFloodProfileTable/{profile_name}"
    debug_info.update({"method": "PUT", "url": url, "body": params})

    if module.check_mode:
        module.exit_json(changed=True, msg="Check mode: profile would be edited", debug_info=debug_info)

    # Try with all params first
    try:
        resp = cc._put(url, json=params)
        debug_info["response_status"] = resp.status_code

        if resp.headers.get("Content-Type") == "application/json":
            data = resp.json()
        else:
            data = {"raw": resp.text}

        if resp.status_code in [200, 204]:
            result["changed"] = True
            result["response"] = data
            debug_info["response_json"] = data
        else:
            error_message = data.get('message', '') if isinstance(data, dict) else ''
            raise Exception(error_message or f"HTTP {resp.status_code} - {resp.text}")

    except Exception as e:
        err_msg = str(e)
        logger.debug(f"Exception message: {err_msg}")
        if 'rsHttpsFloodProfilePacketReporting' in err_msg:
            logger.warning(f"Key rsHttpsFloodProfilePacketReporting not supported, retrying without it for {profile_name}")
            logger.info(f"Retrying PUT without 'rsHttpsFloodProfilePacketReporting' for profile {profile_name}")
            params_wo_packet_report = dict(params)
            params_wo_packet_report.pop('rsHttpsFloodProfilePacketReporting', None)
            try:
              logger.debug(f"PUT {url} with body: {params_wo_packet_report}")
              resp2 = cc._put(url, json=params_wo_packet_report)
              debug_info["retry_without_packet_report"] = params_wo_packet_report
              debug_info["retry_response_status"] = resp2.status_code

              if resp2.headers.get("Content-Type") == "application/json":
                  data2 = resp2.json()
              else:
                  data2 = {"raw": resp2.text}

              if resp2.status_code in [200, 204]:
                  logger.info(f"Profile {profile_name} edited successfully on retry without packet_report")
                  result["changed"] = True
                  result["response"] = data2
                  debug_info["response_json"] = data2
              else:
                  logger.debug(f"Retry failed with status {resp2.status_code}: {resp2.text}")
                  module.fail_json(msg=f"Failed to edit profile (retry without packet_report): HTTP {resp2.status_code}", debug_info=debug_info)
            except Exception as e2:
              logger.debug(f"Exception on retry: {str(e2)}")
              module.fail_json(msg=f"Exception for profile {profile_name} (retry without packet_report): {str(e2)}", debug_info=debug_info, **result)
        else:
            logger.debug(f"Failed to edit profile {profile_name}: {err_msg}")
            module.fail_json(msg=f"Failed to edit profile {profile_name}: {err_msg}", debug_info=debug_info, **result)

    result["debug_info"] = debug_info
    module.exit_json(**result)

def main():
  run_module()

if __name__ == "__main__":
  main()
