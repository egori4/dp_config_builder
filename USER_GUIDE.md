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

# Create connection limit profiles
ansible-playbook playbooks/create_cl_profiles.yml
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

# Alternative: Use standalone example
ansible-playbook playbooks/create_cl_profiles_example.yml --check
```

**Note**: The `cl_protections` section is **optional**. You can skip it entirely and define only `cl_profiles` to create profiles using existing protections already configured on your DefensePro devices.

**Usage patterns**:
- **Create new protections + profiles**: Define both `cl_protections` and `cl_profiles` sections
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

### Connection Limit Profiles
```yaml
# OPTIONAL: Protection subprofiles (only define if creating new ones)
cl_protections:
  - name: "cl_prot_tcp_limit"
    protocol: "6"           # TCP
    threshold: "100"        # Connection limit
    tracking_type: "1"      # Source IP tracking
    risk: "3"              # High risk

# REQUIRED: Profiles (can reference existing or newly created protections)
cl_profiles:
  - name: "web_server_limits"
    protections:
      - "cl_prot_tcp_limit"      # Will be created above
      - "existing_protection"    # Already exists on DefensePro
```

**Examples**:
```yaml
# Example 1: Create new protections + profiles
cl_protections: [...]    # Define new protections
cl_profiles: [...]       # Reference the new protections

# Example 2: Use only existing protections (skip cl_protections entirely)
cl_profiles:
  - name: "profile_with_existing"
    protections:
      - "protection_already_on_device"
      - "another_existing_protection"
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