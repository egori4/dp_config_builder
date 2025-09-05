# DefensePro Configuration Builder - User Guide

**Quick automation for Radware DefensePro syn profile management**

## What This Does

Automate creation, editing, and deletion of DefensePro syn profile across multiple devices using Ansible.

## Quick Start (5 minutes)

### 1. Setup Your Environment
```bash
# Copy configuration templates
# Copy configuration templates
cd vars/
cp cc_example.yml cc.yml                            # Edit variables as needed
cp create_syn_vars.yml.example create_syn_vars.yml  # Edit for your environment
cp edit_syn_vars.yml.example edit_syn_vars.yml      # Edit for your environment
cp delete_syn_vars.yml.example delete_syn_vars.yml  # Edit for your environment
cp get_syn_vars.yml.example get_syn_vars.yml        # Edit for your environment
```

### 2. Run Operations
```bash
# See what SYN Protections exist
ansible-playbook playbooks/get_syn_protection.yml

# Create new SYN Protections
ansible-playbook playbooks/create_syn_protection.yml

# Edit existing SYN Protections
ansible-playbook playbooks/edit_syn_protection.yml

# Delete SYN Protections
ansible-playbook playbooks/delete_syn_protection.yml
```

## Common Workflows

### Workflow 1: Create New syn profile & protection
```bash
# 1. Edit your requirements
nano vars/create_syn_vars.yml

# 2. Test first (dry run)
ansible-playbook --check playbooks/create_syn_protection.yml

# 3. Apply changes
ansible-playbook playbooks/create_syn_protection.yml
```

### Workflow 2: Modify Existing syn protection
```bash
# 1. See current state
ansible-playbook playbooks/get_syn_protection.yml

# 2. Define your changes
nano vars/edit_syn_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/edit_syn_protection.yml

# 4. Apply changes
ansible-playbook playbooks/edit_syn_protection.yml
```

### Workflow 3: delete syn profile and protection
```bash
# 1. Identify what to delete
ansible-playbook playbooks/get_syn_protection.yml

# 2. Define deletions
nano vars/delete_syn_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/delete_syn_protection.yml

# 4. Apply deletions
ansible-playbook playbooks/delete_syn_protection.yml
```

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

### Creating syn profile & protection
```yaml
syn_mappings:
  - profile_name: "Test_10"
    protection_name: "TEST_10"
    protection_params:
      app_port_group: "http"
      activation_threshold: "2500"
      termination_threshold: "1500"
      packet_report: "enable"
```

### Editing syn profile & protection  
```yaml
syn_mappings:
  - profile_name: "Test_20"
    protection_name: "TEST_10"
    protection_id: "500014"
    protection_params:
      app_port_group: "https"
      activation_threshold: "5000"
      termination_threshold: "3000"
      packet_report: "disable"
```

### Deleting syn profile & protection
```yaml
delete_syn:
  - protection_id: "500013"
  - protection_id: "500014"
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
ansible-playbook playbooks/get_syn_profile.yml
```

###  **Test Before Applying**
```bash
ansible-playbook --check playbooks/edit_syn_profile.yml
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
ansible-playbook playbooks/get_syn_profile.yml > backup_$(date +%Y%m%d).log
```

###  **Use Descriptive Names**
```yaml
netclasses:
  - name: "syn_profilename"      # Good: Clear purpose
    # vs
  - name: "syn1"                 # Bad: Unclear
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