# Excel to YAML Converter for DefensePro Configuration

This directory contains Python scripts to convert Excel files into YAML configuration files for DefensePro automation.

## Overview

Instead of manually editing complex YAML files, you can now use Excel spreadsheets to define your DefensePro configuration in a more user-friendly format.

## Scripts

### 1. create_excel_template.py
Generates an Excel template with all required tabs and example data.

```bash
python3 create_excel_template.py -o my_config_template.xlsx
```

### 2. excel_to_yaml_converter.py
Converts a filled Excel file into a YAML configuration file.

```bash
python3 excel_to_yaml_converter.py my_config.xlsx -o create_vars_test.yml
```

## Excel Template Structure

The Excel file contains multiple tabs, each representing a different configuration section:

### Transposed Profile Format
Most profile tabs now use a **transposed format** where:
- **Parameters are in rows** (left column)
- **Profile names are in columns** (allowing easy comparison)
- **Color coding indicates**: Light red = MANDATORY fields, Light blue = OPTIONAL fields
- **Dropdown validation** prevents invalid values

Example BDOS tab structure:
```
Parameter                    | BDOS_Profile_50 | BDOS_Profile_51 | Required
Name                        | BDOS_Profile_50 | BDOS_Profile_51 | MANDATORY
Action                      | report_only     | report_only     | MANDATORY
SYN_Flood                   | enable          | enable          | OPTIONAL
...
```

### Config Tab
- DefensePro device IPs
- Feature enable/disable flags
- Global configuration settings

### Network_Classes Tab
- Network class definitions
- IP address ranges and subnets

### BDOS Tab
- Behavioral DoS profile settings
- Flood detection parameters
- Traffic quotas and thresholds

### DNS Tab
- DNS flood profile settings
- Query rate limits
- Record type quotas

### HTTPS Tab
- HTTPS flood profile settings
- Rate limits and authentication

### OOS Tab (Out-of-State)
- Stateful connection profiles
- Idle state management
- Risk thresholds

### Connection_Limit Tab
- Connection limit protections
- Connection limit profiles
- Rate limiting settings

### Security_Policies Tab
- Security policy definitions
- Profile bindings
- Network assignments

## Usage Workflow

1. **Create Template:**
   ```bash
   cd /home/radware/ansible-lab/dp_config_builder/scripts
   python3 create_excel_template.py -o my_config.xlsx
   ```

2. **Edit Excel File:**
   - Open `my_config.xlsx` in Excel or LibreOffice
   - Fill in your configuration data in each tab
   - Add/remove rows as needed for multiple profiles

3. **Convert to YAML:**
   ```bash
   python3 excel_to_yaml_converter.py my_config.xlsx -o ../vars/create_vars_test.yml
   ```

4. **Run Ansible Playbook:**
   ```bash
   cd ..
   ansible-playbook -i inventory playbooks/create_security_policy.yml -e @vars/create_vars_test.yml
   ```

## Excel Features

### Data Validation
- **Dropdown menus** for all enumerated values (enable/disable, action types, etc.)
- **Prevents typos** and ensures valid configuration values
- **Immediate feedback** when invalid values are entered

### Visual Indicators
- **Light red background**: MANDATORY fields that must be filled
- **Light blue background**: OPTIONAL fields that can be left empty
- **Bold headers**: Clear section identification
- **Auto-sized columns**: Optimal viewing width

### Profile Comparison
- **Side-by-side profiles**: Easy to compare settings between multiple profiles
- **Copy-paste friendly**: Duplicate profiles and modify as needed
- **Scalable**: Add more profile columns as needed

## Excel Column Mappings

### BDOS Profile Columns:
- Name → Profile name
- Action → report_only, block_&_report
- SYN_Flood → enable, disable
- Inbound_Traffic → Traffic limit in kbps
- TCP_In_Quota → TCP quota percentage
- ... (see template for full list)

### Security Policy Columns:
- Policy_Name → Security policy name
- Src_Network → Source network class or "any"
- Dst_Network → Destination network class or "any"
- BDOS_Profile → Reference to BDOS profile name
- Connection_Limit_Profile → Reference to CL profile name
- ... (see template for full list)

## Requirements

```bash
pip3 install openpyxl pyyaml
```

## Tips

1. **Use consistent naming:** Profile names in configuration tabs should match references in Security_Policies tab
2. **Leverage dropdowns:** Use the dropdown arrows to select valid values
3. **Color guidance:** Focus on light red (mandatory) fields first, then fill optional light blue fields
4. **Profile comparison:** Use the transposed format to easily compare settings across profiles
5. **Multiple profiles:** Add new columns for additional profiles of the same type
6. **Comments:** Use the Notes/Description columns for documentation

## Troubleshooting

- **Missing columns:** The converter will skip missing columns and continue processing
- **Invalid values:** Invalid numeric values will be converted to strings
- **Empty tabs:** Tabs with no data are ignored
- **File not found:** Ensure the Excel file path is correct and accessible
