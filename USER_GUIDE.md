# DefensePro Configuration Builder - User Guide

**Quick automation for Radware DefensePro BDoS Profile management**

## What This Does

Automate creation, editing, and deletion of DefensePro BdoS Profile across multiple devices using Ansible.

## Quick Start (5 minutes)

### 1. Setup Your Environment
```bash
# Copy configuration templates
cd vars/
cp cc_example.yml cc.yml                  # Edit credentials as needed
cp create_bdos_vars.yml.example create_bdos_vars.yml
cp edit_bdos_vars.yml.example edit_bdos_vars.yml
cp delete_bdos_vars.yml.example delete_bdos_vars.yml
cp get_bdos_vars.yml.example get_bdos_vars.yml
```

### 2. Run Operations
# See what BDoS profiles exist
ansible-playbook playbooks/get_bdos_profile.yml

# Create new BDoS profiles
ansible-playbook playbooks/create_bdos_profile.yml

# Edit existing BDoS profiles
ansible-playbook playbooks/edit_bdos_profile.yml

# Delete BDoS profiles
ansible-playbook playbooks/delete_bdos_profile.yml
```

## Common Workflows

### Workflow 1: Create New BDoS Profile
# 1. Define your profiles
nano vars/create_bdos_vars.yml

# 2. Dry run first
ansible-playbook --check playbooks/create_bdos_profile.yml

# 3. Apply changes
ansible-playbook playbooks/create_bdos_profile.yml
```

### Workflow 2: Modify Existing BDoS profile
# 1. See current state
ansible-playbook playbooks/get_bdos_profile.yml

# 2. Define changes
nano vars/edit_bdos_vars.yml

# 3. Dry run first
ansible-playbook --check playbooks/edit_bdos_profile.yml

# 4. Apply changes
ansible-playbook playbooks/edit_bdos_profile.yml
```

### Workflow 3: Clean Up bdos profile
# 1. Identify profiles to delete
ansible-playbook playbooks/get_bdos_profile.yml

# 2. Define deletions
nano vars/delete_bdos_vars.yml

# 3. Dry run first
ansible-playbook --check playbooks/delete_bdos_profile.yml

# 4. Apply deletions
ansible-playbook playbooks/delete_bdos_profile.yml
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

### Creating BdoS profile
```yaml
create_bdos:
  - name: "BDOS_Profile1"
    action: 1
    rate_limit: 1000
    rate_limit_status: 1
    challenge_method: 2
    selective_challenge: 2
    collective_challenge: 2
```

### Editing BDoS Profile  
```yaml
edit_bdos:
  - name: "BDOS_Profile1"
    rate_limit: 2000
    rate_limit_status: 1
    challenge_method: 3
```

### Deleting BDoS profile
```yaml
delete_bdos:
  - name: "BDOS_Profile1"
  - name: "BDOS_Profile2"
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
ansible-playbook playbooks/get_bdos_profile.yml
```

###  **Test Before Applying**
```bash
ansible-playbook --check playbooks/edit_bdos_profile.yml
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
ansible-playbook playbooks/get_bdos_profile.yml > backup_$(date +%Y%m%d).log
```

###  **Use Descriptive Names**
```yaml
netclasses:
  - name: "BDoS_Profilename"      # Good: Clear purpose
    # vs
  - name: "BDoS"                 # Bad: Unclear
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