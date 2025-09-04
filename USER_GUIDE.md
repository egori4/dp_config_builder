# DefensePro Configuration Builder - User Guide

**Quick automation for Radware DefensePro network class management**

## What This Does

Automate creation, editing, and deletion of DefensePro profiles and policies across multiple devices using Ansible.

## Quick Start (5 minutes)

### 1. Setup Your Environment
```bash
# Copy configuration templates
cd vars/
cp cc_example.yml cc.yml                    # Edit variables as needed
cp create_vars.yml.example create_vars.yml  # Edit variables as needed
cp edit_vars.yml.example edit_vars.yml      # Edit variables as needed
cp delete_vars.yml.example delete_vars.yml  # Edit variables as needed
cp get_vars.yml.example get_vars.yml        # Edit variables as needed
```

### 2. Run Operations
```bash
# See what network classes exist
ansible-playbook playbooks/get_network_class.yml

# Create new network classes
ansible-playbook playbooks/create_network_class.yml

# Edit existing network classes  
ansible-playbook playbooks/edit_network_class.yml

# Delete network classes
ansible-playbook playbooks/delete_network_class.yml

# Create connection limit profiles (uses create_cl_configuration module)
ansible-playbook playbooks/create_cl_profiles.yml

# Edit existing connection limit protections (uses edit_cl_configuration module)
ansible-playbook playbooks/edit_cl_protections.yml
```

## Common Workflows

### Workflow 1: Create New Network Classes
```bash
# 1. Edit your requirements
nano vars/create_vars.yml

# 2. Test first (dry run)
ansible-playbook --check playbooks/create_network_class.yml

# 3. Apply changes
ansible-playbook playbooks/create_network_class.yml
```

### Workflow 2: Modify Existing Networks
```bash
# 1. See current state
ansible-playbook playbooks/get_network_class.yml

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

### Workflow 4: Create Connection Limit Profiles
```bash
# 1. Configure protections and profiles
nano vars/create_vars.yml

# 2. Test first (dry run)
ansible-playbook --check playbooks/create_cl_profiles.yml

# 3. Apply configuration
ansible-playbook playbooks/create_cl_profiles.yml

# Alternative: Use with check mode for testing
ansible-playbook playbooks/create_cl_profiles.yml --check
```

#### Workflow 4a: Create Protections Only (Skip Profiles)
```bash
# 1. Edit create_vars.yml - define cl_protections section, comment out cl_profiles
nano vars/create_vars.yml

# 2. Test and apply
ansible-playbook --check playbooks/create_cl_profiles.yml
ansible-playbook playbooks/create_cl_profiles.yml
```

#### Workflow 4b: Create Profiles Only (Use Existing Protections)
```bash
# 1. Edit create_vars.yml - comment out cl_protections, define cl_profiles with existing names
nano vars/create_vars.yml

# 2. Test and apply  
ansible-playbook --check playbooks/create_cl_profiles.yml
ansible-playbook playbooks/create_cl_profiles.yml
```

### Workflow 5: Edit Connection Limit Protections
```bash
# 1. Identify existing protections (check DefensePro UI for protection indexes)
# Protection indexes start from 450001 and increment

# 2. Configure your changes (only specify what you want to change)
nano vars/edit_vars.yml

# 3. Test first (dry run) - shows exactly what will change
ansible-playbook --check playbooks/edit_cl_protections.yml

# 4. Apply changes
ansible-playbook playbooks/edit_cl_protections.yml
```

**Note**: For editing, you only need to specify the parameters you want to change. All other parameters remain unchanged on the device.

**Usage patterns**:
- **Create new protections + profiles**: Define both `cl_protections` and `cl_profiles` sections
- **Create protections only**: Define `cl_protections` section, skip `cl_profiles` section
- **Use only existing protections**: Skip `cl_protections`, define only `cl_profiles` with existing protection names
- **Mixed approach**: Create some new protections, reference some existing ones in the same profile

## Configuration Files

### Your Network Devices (`vars/create_vars.yml`, `vars/edit_vars.yml`, etc.)
```yaml
dp_ip:
  - "10.105.192.32"  # Add your DefensePro IPs here
  - "10.105.192.33"
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

## Troubleshooting

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

## Best Practices

###  **Always Discover First**
```bash
ansible-playbook playbooks/get_network_class.yml
```

###  **Test Before Applying**
```bash
ansible-playbook --check playbooks/edit_network_class.yml
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
ansible-playbook playbooks/get_network_class.yml > backup_$(date +%Y%m%d).log
```

###  **Use Descriptive Names**
```yaml
netclasses:
  - name: "web_servers_dmz"      # Good: Clear purpose
    # vs
  - name: "net1"                 # Bad: Unclear
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