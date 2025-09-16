# DefensePro Configuration Builder - User Guide

**Quick automation for Radware DefensePro network class management**

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
# Retrieve DNS profiles
ansible-playbook playbooks/get_dns_profile.yml

# Create new DNS profiles
ansible-playbook playbooks/create_dns_profile.yml

# Edit existing DNS profiles  
ansible-playbook playbooks/edit_dns_profile.yml

# Delete network classes
ansible-playbook playbooks/delete_network_class.yml

# Create connection limit profiles (uses create_cl_configuration module)
ansible-playbook playbooks/create_cl_profiles.yml

# Edit existing connection limit protections (uses edit_cl_configuration module)
ansible-playbook playbooks/edit_cl_protections.yml

# Get connection limit profiles and protections (uses get_cl_configuration module)
ansible-playbook playbooks/get_cl_profiles.yml

# Delete connection limit profiles and protections (uses delete_cl_configuration module)
ansible-playbook playbooks/delete_cl_profiles.yml

# Create security policies with orchestration (includes network classes, CL profiles, and policies)
ansible-playbook playbooks/create_security_policy.yml

# Edit existing security policies (partial updates and profile management)
ansible-playbook playbooks/edit_security_policy.yml
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