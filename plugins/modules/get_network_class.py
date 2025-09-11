<<<<<<< HEAD
# plugins/modules/get_network_class.py
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

documentation = r'''
---
module: get_network_class
short_description: Get the mapping of network classes and groups from a DefensePro device
options:
  provider:
    type: dict
    required: true
  dp_ip:
    type: str
    required: true
'''

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        filter_class_name=dict(type='str', required=False, default=None)
    )

    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)

    try:
        cc = RadwareCC(provider['cc_ip'], provider['username'], provider['password'], log_level=log_level, logger=logger)
        filter_class_name = module.params.get('filter_class_name')
        if filter_class_name:
            url = f"https://{provider['cc_ip']}/mgmt/v2/devices/{module.params['dp_ip']}/config/itemlist/rsBWMNetworkTable/{filter_class_name}"
        else:
            url = f"https://{provider['cc_ip']}/mgmt/v2/devices/{module.params['dp_ip']}/config/itemlist/rsBWMNetworkTable"
        debug_info = {
            'method': 'GET',
            'url': url,
            'body': None
        }
        logger.info(f"Getting network class info for device {module.params['dp_ip']} on cc_ip {provider['cc_ip']}")
        logger.debug(f"Request: {debug_info}")
        resp = cc._get(url)
        logger.debug(f"Response status: {resp.status_code}")
        try:
            data = resp.json()
            logger.debug(f"Response JSON: {data}")
        except ValueError:
            logger.error(f"Invalid JSON response: {resp.text}")
            raise Exception(f"Invalid JSON response: {resp.text}")
        result['response'] = data
        debug_info['response_status'] = resp.status_code
        debug_info['response_json'] = data
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)
    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
=======
# plugins/modules/get_network_class.py
"""
Unified Ansible module to get DefensePro network classes via Radware CyberController API.

This module handles retrieval of network classes with filtering support,
following the unified pattern from other enhanced modules.
"""

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        filter_class_names=dict(type='list', required=False, default=[])
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Extract provider and setup logging
    provider = module.params['provider']
    dp_ip = module.params['dp_ip']
    filter_class_names = module.params['filter_class_names']
    
    log_level = provider.get('log_level', 'disabled')
    
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    debug_info['input'] = {
        'dp_ip': dp_ip,
        'filter_class_names': filter_class_names,
        'filter_count': len(filter_class_names) if filter_class_names else 0
    }
    
    try:
        from ansible.module_utils.radware_cc import RadwareCC
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        # Get network classes from device
        url = f"https://{provider['cc_ip']}/mgmt/v2/devices/{dp_ip}/config/itemlist/rsBWMNetworkTable"
        
        logger.info(f"Getting network class info for device {dp_ip}")
        if filter_class_names:
            logger.info(f"Filtering for class names: {filter_class_names}")
        else:
            logger.info("Getting all network classes (no filter)")
        
        logger.debug(f"Request URL: {url}")
        
        resp = cc._get(url)
        data = resp.json()
        
        logger.debug(f"Response status: {resp.status_code}")
        logger.debug(f"Raw response: {data}")
        
        # Process and filter the response
        network_table = data.get('rsBWMNetworkTable', [])
        
        if filter_class_names:
            # Filter by class names
            filtered_table = []
            for entry in network_table:
                class_name = entry.get('rsBWMNetworkName', '')
                if class_name in filter_class_names:
                    filtered_table.append(entry)
            
            logger.info(f"Filtered {len(network_table)} entries to {len(filtered_table)} matching class names")
            network_table = filtered_table
        else:
            logger.info(f"Retrieved {len(network_table)} network class entries")
        
        # Organize data by class for better structure
        classes_summary = {}
        for entry in network_table:
            class_name = entry.get('rsBWMNetworkName', '')
            if class_name not in classes_summary:
                classes_summary[class_name] = []
            classes_summary[class_name].append(entry)
        
        result['response'] = {
            'rsBWMNetworkTable': network_table,
            'summary': {
                'total_entries': len(network_table),
                'unique_classes': len(classes_summary),
                'class_names': list(classes_summary.keys()),
                'filtered': bool(filter_class_names),
                'filter_applied': filter_class_names if filter_class_names else None
            },
            'classes_breakdown': classes_summary
        }
        
        debug_info['summary'] = {
            'total_entries_retrieved': len(network_table),
            'unique_classes_found': len(classes_summary),
            'filter_applied': bool(filter_class_names),
            'class_names_found': list(classes_summary.keys())
        }
        
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)
    
    result['debug_info'] = debug_info
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
>>>>>>> upstream/main
