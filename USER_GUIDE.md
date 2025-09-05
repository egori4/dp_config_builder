# DefensePro Configuration Builder - User Guide

**Quick automation for Radware DefensePro network class management**

## What This Does

Automate creation, editing, and deletion of DefensePro network classes across multiple devices using Ansible.

## Quick Start (5 minutes)

### 1. Setup Your Environment
```bash
# Copy configuration templates
cd vars/
cp cc_example.yml cc.yml                     # Edit CC connection variables
cp create_dns_vars.yml.example create_dns_vars.yml
cp edit_dns_vars.yml.example edit_dns_vars.yml
cp delete_dns_vars.yml.example delete_dns_vars.yml
cp get_dns_vars.yml.example get_dns_vars.yml
```

### 2. Run Operations
```bash
# Retrieve DNS profiles
ansible-playbook playbooks/get_dns_profile.yml

# Create new DNS profiles
ansible-playbook playbooks/create_dns_profile.yml

# Edit existing DNS profiles  
ansible-playbook playbooks/edit_dns_profile.yml

# Delete DNS profiles
ansible-playbook playbooks/delete_dns_profile.yml
```

## Common Workflows

### Workflow 1: Create New dns profile
```bash
# 1. Edit your requirements
nano vars/create_dns_vars.yml

# 2. Test first (dry run)
ansible-playbook --check playbooks/create_dns_profile.yml

# 3. Apply changes
ansible-playbook playbooks/create_dns_profile.yml
```

### Workflow 2: Modify Existing dns profile
```bash
# 1. See current state
ansible-playbook playbooks/get_dns_profile.yml

# 2. Define your changes
nano vars/edit_dns_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/edit_dns_profile.yml

# 4. Apply changes
ansible-playbook playbooks/edit_dns_profile.yml
```

### Workflow 3: Delete dns profile
```bash
# 1. Identify what to delete
ansible-playbook playbooks/get_dns_profile.yml

# 2. Define deletions
nano vars/delete_dns_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/delete_dns_profile.yml

# 4. Apply deletions
ansible-playbook playbooks/delete_dns_profile.yml
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

### Creating dns profile
```yaml
dns_profile:
  - name: "DNS_Profile_1"
    params:
      DNS Expected Qps: "4000"
      DNS Action: "block & report"
      DNS Max Allow Qps: "4500"
      DNS Manual Trigger Status: "disable"
      DNS Footprint Strictness: "medium"
      DNS Packet Report Status: "enable"
      DNS Learning Suppression Threshold: "50"
```

### Editing dns profile 
```yaml
dns_profile:
  - name: "DNS_Profile_1"
    params:
      DNS Expected Qps: "5000"
      DNS Action: "report"
      DNS Max Allow Qps: "5500"
      DNS Manual Trigger Status: "enable"
```

### Deleting dns profile
```yaml
dns_profiles:
  - name: "DNS_Profile_1"
  - name: "DNS_Profile_2"
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
ansible-playbook playbooks/get_dns_profile.yml
```

###  **Test Before Applying**
```bash
ansible-playbook --check playbooks/edit_dns_profile.yml
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
ansible-playbook playbooks/get_dns_profile.yml > backup_$(date +%Y%m%d).log
```

###  **Use Descriptive Names**
```yaml
netclasses:
  - name: "dns_profilename"      # Good: Clear purpose
    # vs
  - name: "dns1"                 # Bad: Unclear
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