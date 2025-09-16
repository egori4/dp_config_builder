# This file was renamed from edit_cl_protection_multi.py
# ...existing code from edit_cl_protection_multi.py...
"""
Ansible module to edit multiple DefensePro connection limit protection subprofiles via Radware CyberController API (multi-edit, simplified architecture).

Usage:
- Call once per device, passing a list of protections to edit (edit_cl_protections)
- Each protection dict must include protection_index (mandatory), and any parameters to change (partial update)
- All mappings (protocol, action, tracking_type, etc.) are handled internally

Arguments:
  provider (dict): Connection parameters for Radware CyberController
  dp_ip (str): Target DefensePro device IP address
  edit_cl_protections (list): List of dicts, each with protection_index and optional parameters to change

Returns:
  results (list): List of per-protection results (changed, response, debug_info)
  changed (bool): True if any protection was changed
  debug_info (dict): Debug information
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC
from ansible.module_utils.logger import Logger

def run_module():
    PROTOCOL_MAP = {'tcp': '2', 'udp': '3'}
    ATTACK_TYPE_MAP = {'cps': '1', 'concurrent_connections': '2'}
    TRACKING_TYPE_MAP = {'src_ip': '2', 'dst_ip': '3', 'src_and_dest_ip': '4', 'dst_ip_and_port': '5'}
    ACTION_MAP = {'report_only': '0', 'drop': '10'}
    PACKET_REPORT_MAP = {'enable': '1', 'disable': '2'}

    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        edit_cl_protections=dict(type='list', required=True, elements='dict')
    )

    result = dict(changed=False, results=[], debug_info={})
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'], log_level=log_level, logger=logger)
    dp_ip = module.params['dp_ip']
    protections = module.params['edit_cl_protections']
    any_changed = False
    debug_info = {'device': dp_ip, 'protections': []}

    for prot in protections:
        prot_result = dict(changed=False, response={}, debug_info={})
        body = {}
        idx = prot.get('protection_index')
        if idx is None:
            prot_result['debug_info'] = {'error': 'Missing protection_index'}
            debug_info['protections'].append(prot_result['debug_info'])
            continue
        # Map and include only provided parameters
        if 'protection_name' in prot:
            body['rsIDSConnectionLimitAttackName'] = prot['protection_name']
        if 'protocol' in prot:
            try:
                body['rsIDSConnectionLimitAttackProtocol'] = PROTOCOL_MAP[prot['protocol']]
            except KeyError:
                prot_result['debug_info'] = {'error': f"Invalid protocol value: {prot['protocol']}"}
                debug_info['protections'].append(prot_result['debug_info'])
                continue
        if 'app_port_group' in prot:
            body['rsIDSConnectionLimitAttackAppPort'] = prot['app_port_group']
        if 'threshold' in prot:
            body['rsIDSConnectionLimitAttackThreshold'] = prot['threshold']
        if 'tracking_type' in prot:
            try:
                body['rsIDSConnectionLimitAttackTrackingType'] = TRACKING_TYPE_MAP[prot['tracking_type']]
            except KeyError:
                prot_result['debug_info'] = {'error': f"Invalid tracking_type value: {prot['tracking_type']}"}
                debug_info['protections'].append(prot_result['debug_info'])
                continue
        if 'action' in prot:
            try:
                body['rsIDSConnectionLimitAttackReportMode'] = ACTION_MAP[prot['action']]
            except KeyError:
                prot_result['debug_info'] = {'error': f"Invalid action value: {prot['action']}"}
                debug_info['protections'].append(prot_result['debug_info'])
                continue
        if 'packet_report' in prot:
            try:
                body['rsIDSConnectionLimitAttackPacketReport'] = PACKET_REPORT_MAP[prot['packet_report']]
            except KeyError:
                prot_result['debug_info'] = {'error': f"Invalid packet_report value: {prot['packet_report']}"}
                debug_info['protections'].append(prot_result['debug_info'])
                continue
        if 'protection_type' in prot:
            try:
                body['rsIDSConnectionLimitAttackType'] = ATTACK_TYPE_MAP[prot['protection_type']]
            except KeyError:
                prot_result['debug_info'] = {'error': f"Invalid protection_type value: {prot['protection_type']}"}
                debug_info['protections'].append(prot_result['debug_info'])
                continue
        if not body:
            prot_result['debug_info'] = {'error': 'No parameters to update'}
            debug_info['protections'].append(prot_result['debug_info'])
            continue
        path = f"/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable/{idx}"
        url = f"https://{provider['cc_ip']}{path}"
        prot_result['debug_info'] = {'method': 'PUT', 'url': url, 'body': body}
        logger.info(f"Editing connection limit protection at index {idx} on device {dp_ip}")
        logger.debug(f"Request: {prot_result['debug_info']}")
        if not module.check_mode:
            try:
                resp = cc._put(url, json=body)
                prot_result['debug_info']['response_status'] = resp.status_code
                data = resp.json()
                prot_result['response'] = data
                prot_result['changed'] = True
                any_changed = True
                prot_result['debug_info']['response_json'] = data
            except Exception as e:
                logger.error(f"Exception: {str(e)}")
                prot_result['debug_info']['error'] = str(e)
        result['results'].append(prot_result)
        debug_info['protections'].append(prot_result['debug_info'])
    result['changed'] = any_changed
    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
