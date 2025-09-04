# DefensePro Configuration Builder - User Guide

**Quick automation for Radware DefensePro ssl object management**

## What This Does

Automate creation, editing, and deletion of DefensePro ssl object across multiple devices using Ansible.

## Quick Start (5 minutes)

### 1. Setup Your Environment
```bash
# Copy configuration templates
cd vars/
cp cc_example.yml cc.yml                     # Edit CyberController details
cp create_ssl_vars.yml.example create_ssl_vars.yml  # Define objects to create
cp edit_ssl_vars.yml.example edit_ssl_vars.yml      # Define objects to edit
cp delete_ssl_vars.yml.example delete_ssl_vars.yml  # Define objects to delete
cp get_ssl_vars.yml.example get_ssl_vars.yml        # Define objects to fetch

```

### 2. Run Operations
```bash
# Fetch SSL object(s)
ansible-playbook playbooks/get_ssl_object.yml

# Create new SSL object(s)
ansible-playbook playbooks/create_ssl_object.yml

# Edit existing SSL object(s)
ansible-playbook playbooks/edit_ssl_object.yml

# Delete SSL object(s)
ansible-playbook playbooks/delete_ssl_object.yml
```

## Common Workflows

### Workflow 1: Create New ssl object
```bash
# 1. Define SSL objects
nano vars/create_ssl_vars.yml

# 2. Test first (dry run)
ansible-playbook --check playbooks/create_ssl_object.yml

# 3. Apply changes
ansible-playbook playbooks/create_ssl_object.yml
```

### Workflow 2: Modify Existing ssl object
```bash
# 1. Fetch current state
ansible-playbook playbooks/get_ssl_object.yml

# 2. Define changes
nano vars/edit_ssl_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/edit_ssl_object.yml

# 4. Apply changes
ansible-playbook playbooks/edit_ssl_object.yml
```

### Workflow 3: Delete ssl object
```bash
# 1. Identify SSL objects
ansible-playbook playbooks/get_ssl_object.yml

# 2. Define deletions
nano vars/delete_ssl_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/delete_ssl_object.yml

# 4. Apply deletions
ansible-playbook playbooks/delete_ssl_object.yml
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

### Creating ssl object
```yaml
ssl_objects:
  - ssl_object_name: "server1"
    params:
      ssl_object_profile: "enable"   # enable/disable
      IP_Address: "155.1.102.7"
      Port: 443
```

### Editing ssl object  
```yaml
ssl_objects_to_edit:
  - ssl_object_name: "server1"
    params:
      ssl_object_profile: "enable"
      IP_Address: "155.1.102.15"
      Port: 443
```

### Deleting ssl object
```yaml
delete_ssl_object:
  - ssl_object_name: "server1"
  - ssl_object_name: "server2"
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
ansible-playbook playbooks/get_ssl_object.yml
```

###  **Test Before Applying**
```bash
ansible-playbook --check playbooks/edit_ssl_object.yml
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
ansible-playbook playbooks/get_ssl_object.yml > backup_$(date +%Y%m%d).log
```

###  **Use Descriptive Names**
```yaml
ssl_objects:
  - ssl_object_name: "server1_https"      # Good: Clear purpose
    # vs
  - name: "ssl_object"                 # Bad: Unclear
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