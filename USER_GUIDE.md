# DefensePro Configuration Builder - User Guide

**Quick automation for Radware DefensePro https profile management**

## What This Does

Automate creation, editing, and deletion of DefensePro http profile across multiple devices using Ansible.

## Quick Start (5 minutes)

### 1. Setup Your Environment
```bash
# Copy configuration templates
cd vars/
cp cc_example.yml cc.yml                      # Edit CyberController connection details
cp create_https_vars.yml.example create_https_vars.yml   # Edit HTTPS profile creation variables
cp edit_https_vars.yml.example edit_https_vars.yml       # Edit HTTPS profile editing variables
cp delete_https_vars.yml.example delete_https_vars.yml   # Edit HTTPS profile deletion variables
cp get_https_vars.yml.example get_https_vars.yml         # Edit HTTPS profile fetch variables

```

### 2. Run Operations
```bash
# See what HTTPS profiles exist
ansible-playbook playbooks/get_http_profile.yml

# Create new HTTPS profiles
ansible-playbook playbooks/create_http_profile.yml

# Edit existing HTTPS profiles
ansible-playbook playbooks/edit_http_profile.yml

# Delete HTTPS profiles
ansible-playbook playbooks/delete_http_profile.yml
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
nano vars/edit_https_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/edit_http_profile.yml

# 4. Apply changes
ansible-playbook playbooks/edit_http_profile.yml
```

### Workflow 3: Clean Up Http Profile
```bash
# 1. Identify profiles to delete
ansible-playbook playbooks/get_http_profile.yml

# 2. Define deletions
nano vars/delete_https_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/delete_http_profile.yml

# 4. Apply deletions
ansible-playbook playbooks/delete_http_profile.yml
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

### Creating Http Profile
```yaml
https_mappings:
  - name: "HTTPS_Profile_1"
    params:
      Profile Action: "block & report"        # report / block & report
      Rate Limit: "100000"                    # Max packets per second
      Selective Challenge: "enable"           # enable / disable
      Collective Challenge: "enable"          # enable / disable
      Challenge Method: "httpRedirect"        # javaScript / httpRedirect
      Rate Limit Status: "disable"            # enable / disable
      Full Session Decryption: "disable"      # enable / disable

```

### Editing Http Profile  
```yaml
edit_https_mappings:
  - name: "HTTPS_Profile_1"
    params:
      Profile Action: "report"
      Rate Limit: "50000"
      Selective Challenge: "disable"
      Collective Challenge: "enable"
      Challenge Method: "javaScript"
      Rate Limit Status: "enable"
      Full Session Decryption: "enable"
```

### Deleting Http Profile
```yaml
delete_https_mappings:
  - "HTTPS_Profile_1"
  - "HTTPS_Profile_2"
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