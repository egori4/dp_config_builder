# DefensePro Configuration Builder - User Guide

**Quick automation for Radware DefensePro https profile management**

## What This Does

Automate creation, editing, and deletion of DefensePro profiles and policies across multiple devices using Ansible.

## Prerequisites

Before starting, ensure your Ansible environment is properly configured:

### Required Files Setup
```bash
# 1. Create Ansible configuration (required)
cp ansible_example.cfg ansible.cfg

# 2. Create inventory file (required) 
cp inventory_example.ini inventory.ini

# 3. Create CyberController connection settings (required)
cd vars/
cp cc_example.yml cc.yml
nano cc.yml  # Edit with your CyberController IP, username, password

```

### Verify Setup

# Test inventory
ansible-inventory --list
```

## Quick Start (5 minutes)

### 1. Setup Your Environment
```bash
# Copy configuration templates (after completing Prerequisites above)
cd vars/
cp create_vars.yml.example create_vars.yml  # Edit variables as needed
cp edit_vars.yml.example edit_vars.yml      # Edit variables as needed
cp delete_vars.yml.example delete_vars.yml  # Edit variables as needed
cp get_vars.yml.example get_vars.yml        # Edit variables as needed
cp update_vars_example.yml update_vars.yml  # Edit variables as needed
```

### 2. Run Operations
```bash
# See what HTTPS profiles exist
ansible-playbook playbooks/get_http_profile.yml

# Create new HTTPS profiles
ansible-playbook playbooks/create_http_profile.yml

# Edit existing HTTPS profiles
ansible-playbook playbooks/edit_http_profile.yml

# Delete network classes
ansible-playbook playbooks/delete_network_class.yml
```

## Common Workflows

### Workflow 1: Create New Http profile
```bash
# 1. Edit your requirements
nano vars/create_http_vars.yml

# 2. Test first (dry run)
ansible-playbook --check playbooks/create_http_profile.yml

# 3. Apply changes
ansible-playbook playbooks/create_http_profile.yml
```

### Workflow 2: Modify Existing Http Profile
```bash
# 1. See current state
ansible-playbook playbooks/get_http_profile.yml

# 2. Define your changes
nano vars/edit_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/edit_network_class.yml

# 4. Apply changes
ansible-playbook playbooks/edit_network_class.yml
```

### Workflow 3: Clean Up Networks
```bash
# 1. Identify what to delete
ansible-playbook playbooks/get_network_class.yml

# 2. Define deletions
nano vars/delete_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/delete_network_class.yml

# 4. Apply deletions
ansible-playbook playbooks/delete_network_class.yml
```

## Configuration Files

### Your Network Devices (`vars/create_vars.yml`, `vars/edit_vars.yml`, `vars/get_vars.yml`, etc.)
```yaml
dp_ip:
  - "10.105.192.32"  # Add your DefensePro IPs here
  - "10.105.192.33"

# For getting network classes (get_vars.yml)
filter_class_names: []  # Show all classes (default)
# filter_class_names: ["web_servers", "db_servers"]  # Filter specific classes

# For getting profiles (get_vars.yml)
filter_cl_profile_names: []  # Show all profiles (default)
# filter_cl_profile_names: ["profile1", "profile2"]  # Filter specific profiles
```

### CyberController Connection (`vars/cc.yml`)
```yaml
cc_ip: "10.105.193.3"
username: "your_username"
password: "your_password"
log_level: "info"  # info, debug, or disabled
```

## Variable Format Guide

### Creating Networks
```yaml
netclasses:
  - name: "web_servers"
    groups:
      - { address: "192.168.1.0", mask: "255.255.255.0" }
      - { address: "192.168.2.0", mask: "24" }
```

### Editing Networks  
```yaml
edit_networks:
  - {class_name: "web_servers", index: 0, address: "10.1.1.0", mask: "24"}
  - {class_name: "web_servers", index: 1, address: "10.1.2.0", mask: "24"}
```

### Deleting Networks
```yaml
delete_networks:
  - {class_name: "web_servers", index: 0}
  - {class_name: "old_servers", index: 1}
```

### Connection Limit Profiles - Complete Configuration Reference

**Important**: Both `cl_protections` and `cl_profiles` sections are completely optional. You can define one, another or both, based on your needs.

#### Creating Connection Limit Protections (ALL Supported Parameters)
```yaml
# OPTIONAL: Protection subprofiles (only define if creating new ones)
cl_protections:
  - name: "cl_prot_comprehensive_example"        # MANDATORY: Protection name
    protocol: "tcp"                              # OPTIONAL: tcp, udp (default: tcp)
    threshold: "100"                             # OPTIONAL: Connection threshold (default: "50")
    app_port_group: "https"                      # OPTIONAL: http, https, dns, ftp, smtp, imap, custom port, or "" for all (default: "")
    tracking_type: "src_ip"                      # OPTIONAL: src_ip, dst_ip, src_and_dest_ip, dst_ip_and_port (default: dst_ip)
    action: "drop"                               # OPTIONAL: drop, report_only (default: drop)
    packet_report: "enable"                      # OPTIONAL: enable, disable (default: disable)
    protection_type: "cps"                       # OPTIONAL: cps, concurrent_connections (default: cps)
    index: 450001                                # OPTIONAL: 0 or 450001+ (default: 0)

  # Minimal example (only mandatory parameter)
  - name: "cl_prot_minimal"                      # MANDATORY: Only this is required
    # All other parameters will use defaults

  # Custom index example
  - name: "cl_prot_custom_index"
    protocol: "udp"
    threshold: "200"
    index: 450002                                # Custom index
```

#### Editing Connection Limit Protections (Partial Updates)
```yaml
# Edit existing protections - ONLY specify what you want to change
edit_cl_protections:
  - protection_index: 450001                    # MANDATORY: Must specify which protection to edit
    protection_name: "Updated Protection"        # OPTIONAL: Change name only
    
  - protection_index: 450002                    # MANDATORY: Another protection to edit
    threshold: "500"                            # OPTIONAL: Change threshold only
    action: "report_only"                       # OPTIONAL: Change action only
    # All other parameters remain unchanged
    
  - protection_index: 450003                    # MANDATORY: Edit multiple parameters
    protocol: "udp"                             # OPTIONAL: Change protocol
    threshold: "300"                            # OPTIONAL: Change threshold
    tracking_type: "dst_ip_and_port"           # OPTIONAL: Change tracking
    packet_report: "disable"                   # OPTIONAL: Change reporting
    # Other parameters remain unchanged
```

#### Getting Connection Limit Profiles and Protections
```yaml
# Get all profiles and protections from devices
# No configuration needed - just run the playbook
ansible-playbook playbooks/get_cl_profiles.yml

# Filter by specific profile names (configure in get_vars.yml)
filter_cl_profile_names: ["profile1", "profile2"]  # Show only these profiles
# filter_cl_profile_names: []                      # Show all profiles (default)
```

#### Deleting Connection Limit Profiles and Protections
```yaml
# OPTIONAL: Remove protections from profiles (without deleting protection itself)
cl_profile_deletions:
  - profile_name: "profile_to_modify"
    protections:
      - "protection1"
      - "protection2"

# OPTIONAL: Delete protections entirely (protection must not be in any profile)
cl_protection_deletions:
  - protections_to_delete:
      - "standalone_protection"      # Delete by name (module looks up index)
      - "another_protection"         # Delete by name (module looks up index)
      - "old_protection"             # Delete by name (module looks up index)
      - 450001                       # Delete by index directly
      - 450002                       # Delete by index directly

# Important: Both sections are optional - define based on your needs
# Order: Profile deletions processed first, then protection deletions
```

**Parameter Reference for Connection Limit Protections**:

| Parameter | Status | Options | Default | Description |
|-----------|--------|---------|---------|-------------|
| `name` | **MANDATORY** | Any string | - | Protection name (create only) |
| `protection_index` | **MANDATORY** | Integer | - | Index to edit (edit only) |
| `protocol` | OPTIONAL | tcp, udp | tcp | Network protocol |
| `threshold` | OPTIONAL | "number" | "50" | Connection limit threshold |
| `app_port_group` | OPTIONAL | http, https, dns, ftp, smtp, imap, custom port, "" | "" | Application port filter |
| `tracking_type` | OPTIONAL | src_ip, dst_ip, src_and_dest_ip, dst_ip_and_port | dst_ip | Traffic tracking method |
| `action` | OPTIONAL | drop, report_only | drop | Action when threshold exceeded |
| `packet_report` | OPTIONAL | enable, disable | disable | Detailed packet reporting |
| `protection_type` | OPTIONAL | cps, concurrent_connections | cps | Detection type |
| `index` | OPTIONAL | 0 or 450001+ | 0 | Creation index |

**Key Points for Editing**:
-  **Partial Updates**: Only specify parameters you want to change
-  **Unchanged Values**: Unspecified parameters keep their current values
-  **Flexible**: Change one parameter or many in a single operation

#### Connection Limit Profiles (Optional Section)
```yaml
# OPTIONAL: Profiles (can reference existing or newly created protections)
cl_profiles:
  - name: "web_server_limits"                   # MANDATORY: Profile name
    protections:                                # MANDATORY: List of protections
      - "cl_prot_tcp_limit"                     # Will be created above
      - "existing_protection"                   # Already exists on DefensePro
      
  - name: "database_limits"                     # Another profile example
    protections:
      - "cl_prot_comprehensive_example"         # Reference created protection
      - "legacy_protection_on_device"           # Reference existing protection
```

**Profile Configuration Notes**:
-  **name**: MANDATORY - Unique profile name
-  **protections**: MANDATORY - List of protection names to include
-  **Mixed References**: Can combine newly created and existing protections
-  **Flexible**: Create profiles with any combination of protections
#### Usage Pattern Examples
```yaml
# Example 1: Create new protections + profiles (comprehensive)
cl_protections:
  - name: "web_protection"
    protocol: "tcp"
    threshold: "100"
    app_port_group: "https"
    tracking_type: "src_ip"
    action: "drop"
    index: 450001
  - name: "api_protection"
    protocol: "tcp"
    threshold: "500"
    tracking_type: "dst_ip_and_port"
    action: "report_only"
    index: 450002

cl_profiles:
  - name: "web_security_profile"
    protections:
      - "web_protection"      # Newly created
      - "api_protection"      # Newly created

# Example 2: Use only existing protections (skip cl_protections entirely)
cl_profiles:
  - name: "profile_with_existing"
    protections:
      - "protection_already_on_device"
      - "another_existing_protection"

# Example 3: Mixed approach (some new, some existing)
cl_protections:
  - name: "new_custom_protection"
    protocol: "udp"
    threshold: "200"
    index: 450003

cl_profiles:
  - name: "mixed_profile"
    protections:
      - "new_custom_protection"      # Newly created above
      - "legacy_protection"          # Already exists on device
```

### Security Policy Configuration

Configure security policies with profile bindings in `vars/create_vars.yml`:

```yaml
# Orchestration control flags
security_policy_config:
  create_network_classes: true     # Create network classes first
  create_cl_profiles: true         # Create CL profiles next
  create_security_policies: true   # Create security policies last

# Security policies with profile bindings
security_policies:
  - policy_name: "web_server_protection"
    state: "enable"                        # enable, disable
    action: "block_and_report"                        # block_and_report, report_only
    src_network: "any"                     # Source network class
    dst_network: "web_servers"             # Destination network class  
    direction: "oneway"                    # oneway, twoway
    priority: "100"                        # Policy priority (lower = higher precedence)
    packet_reporting_status: "enable"      # enable, disable
    
    # Profile bindings (all optional)
    connection_limit_profile: "web_cl_profile"
    bdos_profile: "default_netflood_profile"
    syn_protection_profile: "default_syn_profile"
    dns_flood_profile: ""                  # Empty = no binding
    https_flood_profile: ""
    traffic_filters_profile: ""
    signature_protection_profile: "web_appsec_profile"
    ert_attackers_feed_profile: ""
    geo_feed_profile: ""
    out_of_state_profile: ""
```

**Security Policy Configuration Notes**:
- **policy_name**: MANDATORY - Unique policy name
- **src_network, dst_network**: MANDATORY - Network class names (use "any" for any network)
- **direction**: MANDATORY - Traffic direction to match
- **Profile bindings**: All optional - leave empty string for no binding
- **Control flags**: Use to enable/disable each creation stage independently

### Editing Security Policies

Modify existing security policies using partial updates in `vars/edit_vars.yml`:

```yaml
# Target DefensePro devices
dp_ip:
  - "10.105.192.32"

# Security policies to edit
edit_security_policies:
  - policy_name: "web_server_protection"    # MANDATORY: Policy name to edit
    # Basic configuration parameters (all optional)
    src_network: "internal_networks"        # Source network class name or "any"
    dst_network: "web_servers"              # Destination network class name or "any"
    direction: "twoway"                     # oneway, twoway, bidirectional
    state: "enable"                         # enable, disable, active, inactive
    action: "block_and_report"              # block_and_report, report_only
    priority: "750"                         # Priority value (1-1000)
    packet_reporting_status: "enable"       # enable, disable
    
    # Profile bindings (all optional - use empty string to remove binding)
    connection_limit_profile: "web_limits"  # Connection limit profile name
    bdos_profile: ""                        # BDOS profile name (empty = detach)
    syn_protection_profile: "syn_limits"    # SYN protection profile name
    dns_flood_profile: ""                   # DNS flood profile name
    https_flood_profile: ""                 # HTTPS flood profile name
    traffic_filters_profile: ""             # Traffic filters profile name
    signature_protection_profile: "app_sec" # Application security profile name
    ert_attackers_feed_profile: ""          # ERT attackers feed profile name
    geo_feed_profile: ""                    # Geo feed profile name
    out_of_state_profile: ""                # Out of state profile name

  # Edit another policy - minimal changes
  - policy_name: "database_protection"
    action: "report_only"                   # Change to monitoring mode
    connection_limit_profile: ""            # Remove connection limit protection
```

**Run the playbook**:
```bash
# Preview changes (check mode)
ansible-playbook -i inventory.ini playbooks/edit_security_policy.yml --check

# Execute changes
ansible-playbook -i inventory.ini playbooks/edit_security_policy.yml
```

**Security Policy Editing Notes**:
- **policy_name**: MANDATORY - Must be an existing security policy name
- **Partial Updates**: Only specify parameters you want to change - unspecified parameters remain unchanged
- **Profile Detachment**: Use empty string ("") to remove profile bindings
- **Profile Attachment**: Specify profile name to attach/change binding  
- **Preview Mode**: Use `--check` flag to see planned changes before execution
- **Control Flags**: Device locking can be skipped with `skip_device_lock: true` in vars

### Deleting Security Policies

Remove security policies with optional profile cleanup using `vars/delete_vars.yml`:

```yaml
# Target DefensePro devices
dp_ip:
  - "10.105.192.32"

# Security policies to delete
delete_security_policies:
  - policy_name: "test_security_policy"     # MANDATORY: Policy name to delete
    deletion_mode: "policy_only"            # OPTIONAL: policy_only | policy_and_profiles
  
  - policy_name: "old_security_policy"     # MANDATORY: Policy name to delete  
    deletion_mode: "policy_and_profiles"    # OPTIONAL: Advanced cleanup mode
    
  # deletion_mode defaults to "policy_only" if not specified
  - policy_name: "another_policy"           # Uses default safe deletion mode
```

**Deletion Modes**:

1. **`policy_only` (default)**:
   - Safe deletion - only removes the security policy
   - Associated profiles remain available for other policies
   - Use for most deletion scenarios

2. **`policy_and_profiles` (advanced)**:
   - May remove associated profiles if no longer used by other policies
   - Use with caution - may affect other policies
   - Only use when certain about profile cleanup requirements

**Usage Examples**:
```bash
# Delete policies with preview mode (recommended first step)
ansible-playbook playbooks/delete_security_policy.yml --check

# Delete policies (actual execution)
ansible-playbook playbooks/delete_security_policy.yml

# Delete with verbose output
ansible-playbook playbooks/delete_security_policy.yml -v
```

**Security Policy Deletion Notes**:
- **policy_name**: MANDATORY - Must be an existing security policy name
- **deletion_mode**: OPTIONAL - Defaults to "policy_only" for safety
- **Safe Default**: Always use "policy_only" unless certain about profile cleanup needs
- **Preview Mode**: Use `--check` flag to see planned deletions before execution
- **Batch Processing**: Multiple policies can be deleted in a single operation
- **Profile Safety**: "policy_only" mode preserves profiles for other policies to use
- **Advanced Cleanup**: "policy_and_profiles" mode should only be used when profiles are policy-specific

**Recommended Workflow**:
1. Use preview mode first: `ansible-playbook playbooks/delete_security_policy.yml --check`
2. Review planned deletions carefully
3. For shared environments, prefer "policy_only" mode
4. For standalone policies with unique profiles, consider "policy_and_profiles" mode
5. Execute deletion: `ansible-playbook playbooks/delete_security_policy.yml`

## Troubleshooting

### "No inventory" or "module not found" errors
```bash
# Check if required files exist
ls -la ansible.cfg inventory.ini

# Create if missing (see Prerequisites section)
cp ansible_example.cfg ansible.cfg
cp inventory_example.ini inventory.ini

# Verify Ansible can find modules
ansible-doc -l | grep network_class
```

### "File not found" errors
```bash
# Copy the example files
cp vars/create_vars.yml.example vars/create_vars.yml
# Then edit with your details
```

### "Connection failed" errors  
```bash
# Check your cc.yml file
cat vars/cc.yml
# Verify IP, username, password are correct
```

### "Variable undefined" errors
```bash
# Ensure all required variables are set in your vars files
# Check the .example files for required format
```

### "ansible-playbook command not found"
```bash
# Install Ansible if not already installed
pip3 install ansible

# Or using package manager
sudo apt-get install ansible  # Ubuntu/Debian
sudo yum install ansible      # CentOS/RHEL
```

### "Protection deletion failed" errors
```bash
# Check if protection is still associated with any profile
ansible-playbook playbooks/get_cl_profiles.yml

# Remove protection from profiles first, then delete protection
# Edit delete_vars.yml - define both sections if doing complete cleanup
```

## Best Practices

###  **Always Discover First**
```bash
ansible-playbook playbooks/get_http_profile.yml
```

###  **Test Before Applying**
```bash
ansible-playbook --check playbooks/edit_http_profile.yml
```

###  **Start with One Device**
```yaml
# Test on single device first
dp_ip:
  - "10.105.192.32"  # Test device only
```

###  **Keep Backups**
```bash
# Save current state before major changes
ansible-playbook playbooks/get_http_profile.yml > backup_$(date +%Y%m%d).log
```

###  **Use Descriptive Names**
```yaml
Http Profile:
  - name: "Http_profilename"      # Good: Clear purpose
    # vs
  - name: "Http"                 # Bad: Unclear
```

## Getting Help

1. **Check the example files** - They have detailed comments
2. **Use dry run mode** - Test with `--check` flag first  
3. **Check logs** - Look in `playbooks/log/` directory
4. **Validate syntax** - `python3 -c "import yaml; yaml.safe_load(open('vars/edit_vars.yml'))"`

---

**Need technical details?** See [DEVELOPER.md](DEVELOPER.md) for module architecture, API endpoints, and development information.

## Maintainer & Contact

**Project Maintainer**: [Egor Egorov]  
**Email**: [egore@radware.com]  
**GitHub Radware**: [@rdwr-egore](https://github.com/rdwr-egore)
**GitHub Private**: [@egori4](https://github.com/egori4)

**Contributor**:  [@rahulku25](https://github.com/rahulku25)