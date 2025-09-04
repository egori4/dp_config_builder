# DefensePro Configuration Builder - User Guide

**Quick automation for Radware DefensePro OOS Profile management**

## What This Does

Automate creation, editing, and deletion of DefensePro OOS Profile across multiple devices using Ansible.

## Quick Start (5 minutes)

### 1. Setup Your Environment
```bash
# Copy configuration templates
cd vars/
cp cc_example.yml cc.yml                    # Edit connection variables as needed
cp create_oos_vars.yml.example create_oos_vars.yml  # For creating profiles
cp edit_oos_vars.yml.example edit_oos_vars.yml      # For editing profiles
cp delete_oos_vars.yml.example delete_oos_vars.yml  # For deleting profiles
cp get_oos_vars.yml.example get_oos_vars.yml        # For fetching profiles
```

### 2. Run Operations
```bash
# Fetch OOS profiles
ansible-playbook playbooks/get_oos_profile.yml

# Create new OOS profiles
ansible-playbook playbooks/create_oos_profile.yml

# Edit existing OOS profiles
ansible-playbook playbooks/edit_oos_profile.yml

# Delete OOS profiles
ansible-playbook playbooks/delete_oos_profile.yml
```

## Common Workflows

### Workflow 1: Create New OOS Profile
```bash
# 1. Edit your requirements
nano vars/create_oos_vars.yml

# 2. Test first (dry run)
ansible-playbook --check playbooks/create_oos_profile.yml

# 3. Apply changes
ansible-playbook playbooks/create_oos_profile.yml

```

### Workflow 2: Modify Existing OOS Profile
```bash
# 1. See current profiles
ansible-playbook playbooks/get_oos_profile.yml

# 2. Define your changes
nano vars/edit_oos_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/edit_oos_profile.yml

# 4. Apply changes
ansible-playbook playbooks/edit_oos_profile.yml
```

### Workflow 3: Delete OOS Profile
```bash
# 1. Identify what to delete
ansible-playbook playbooks/get_oos_profile.yml

# 2. Define deletions
nano vars/delete_oos_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/delete_oos_profile.yml

# 4. Apply deletions
ansible-playbook playbooks/delete_oos_profile.yml
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

### Creating OOS Profile
```yaml
oos_profiles:
  - name: "OOS_Profile_1"
    params:
      Act Threshold: "5000"
      Term Threshold: "4000"
      Syn-Ack Allow: "enable"
      Packet Trace Status: "enable"
      Packet Report Status: "enable"
      Action: "block & report"
```

### Editing Networks  
```yaml
oos_profiles:
  - name: "OOS_Profile_1"
    params:
      Act Threshold: "6000"
      Term Threshold: "5000"
      Syn-Ack Allow: "disable"
      Packet Trace Status: "enable"
      Packet Report Status: "disable"
      Action: "block & report"
```

### Deleting Networks
```yaml
delete_oos_profiles:
  - "OOS_Profile_1"
  - "OOS_Profile_2"
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
ansible-playbook playbooks/get_oos_profile.yml
```

###  **Test Before Applying**
```bash
ansible-playbook --check playbooks/edit_oos_profile.yml
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
ansible-playbook playbooks/get_oos_profile.yml > backup_$(date +%Y%m%d).log
```

###  **Use Descriptive Names**
```yaml
oos_profile:
  - name: "oos_profilename"      # Good: Clear purpose
    # vs
  - name: "OOS1"                 # Bad: Unclear
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