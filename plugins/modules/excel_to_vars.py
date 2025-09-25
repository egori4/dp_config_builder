#!/usr/bin/python
# plugins/modules/excel_to_vars.py
"""
Ansible module to convert Excel configuration to YAML variables.

This module wraps the excel_to_yaml_converter.py script functionality
to enable dynamic conversion from Excel files to YAML variables within playbooks.
"""


import os
import sys
import subprocess
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.logger import Logger

def run_module():
    """Main module execution function"""
    
    # Define available arguments/parameters that a user can pass to the module

    # Set default output_file to '../vars/create_vars.yml' (one level above playbooks)
    module_args = dict(
        provider=dict(type='dict', required=True),
        excel_file=dict(type='str', required=True),
        output_file=dict(type='str', required=False, default=os.path.join('..', 'vars', 'create_vars.yml')),
        return_content=dict(type='bool', required=False, default=False)
    )


    # Initialize result dictionary
    result = dict(
        changed=False,
        content={},
        output_file='',
        message=''
    )



    # Create AnsibleModule object
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Get parameters
    provider = module.params['provider']
    excel_file = os.path.join('..', module.params['excel_file'])
    output_file = module.params['output_file']
    return_content = module.params['return_content']

    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    logger.info("excel_to_vars module started", indent=0)
    logger.debug(f"Parameters: excel_file={excel_file}, output_file={output_file}, return_content={return_content}, log_level={log_level}", indent=1)

    # Validate Excel file exists

    if not os.path.exists(excel_file):
        logger.error(f"Excel file not found: {excel_file}")
        module.fail_json(msg=f"Excel file not found: {excel_file}")


    try:
        # Set default output file to vars/create_vars.yml if not specified
        if not output_file:
            output_file = os.path.join('..', 'vars', 'create_vars.yml')
        # Make sure output path is absolute relative to current working directory
        if not os.path.isabs(output_file):
            output_file = os.path.abspath(output_file)

        script_path = os.path.join('..', 'scripts', 'excel_to_yaml_converter.py')

        # Perform the conversion by calling the script directly
        if not module.check_mode:
            cmd = [sys.executable, script_path, excel_file, '-o', output_file]
            logger.info(f"Running converter: {' '.join(cmd)}", indent=1)
            result_proc = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
            logger.debug(f"Converter stdout: {result_proc.stdout}", indent=2)
            logger.debug(f"Converter stderr: {result_proc.stderr}", indent=2)
            if result_proc.returncode != 0:
                logger.error(f"Excel conversion failed: {result_proc.stderr}")
                module.fail_json(msg=f"Excel conversion failed: {result_proc.stderr}")
            result['changed'] = True
            result['message'] = f"Successfully converted {excel_file} to {output_file}"
            logger.info(result['message'], indent=1)
        else:
            logger.info(f"Check mode: Would convert {excel_file} to {output_file}", indent=1)
            result['message'] = f"Would convert {excel_file} to {output_file}"

        result['output_file'] = output_file

        # If requested, read the content and return as structured data
        if return_content and not module.check_mode:
            try:
                import yaml
                with open(output_file, 'r') as f:
                    content = yaml.safe_load(f)
                result['content'] = content
                logger.debug(f"Loaded YAML content from {output_file}", indent=2)
            except Exception as e:
                logger.warning(f"Could not parse generated YAML content: {e}")

    except Exception as e:
        logger.error(f"Failed to convert Excel file: {str(e)}")
        module.fail_json(msg=f"Failed to convert Excel file: {str(e)}")

    # Return results
    logger.info("excel_to_vars module completed", indent=0)
    module.exit_json(**result)

def main():
    """Entry point for the module"""
    run_module()

if __name__ == '__main__':
    main()

def main():
    """Entry point for the module"""
    run_module()

if __name__ == '__main__':
    main()