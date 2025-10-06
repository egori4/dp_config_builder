# DefensePro Configuration Builder - User Guide

**Complete workflows and configuration guide for DefensePro automation**

## 🎯 What This Guide Covers

Step-by-step workflows for automating DefensePro configuration management:
- **Network Classes**: Create, edit, delete, and query network classifications
- **Security Profiles**: Manage Connection Limit, BDoS, DNS, HTTPS, OOS, SSL Objects, Traffic Filter profiles  
- **Security Policies**: Orchestrated creation with profile binding
- **Device Operations**: Locking, configuration updates, and policy application

## 📋 Prerequisites

Complete these setup steps before following any workflows:

### 1. Required Files Setup
```bash
# Create Ansible configuration files
cp ansible_example.cfg ansible.cfg
cp inventory_example.ini inventory.ini

# Create variable templates  
cd vars/
cp cc_example.yml cc.yml                    # CyberController connection
cp create_vars.yml.example create_vars.yml  # Creation workflows
cp edit_vars.yml.example edit_vars.yml      # Editing workflows
cp delete_vars.yml.example delete_vars.yml  # Deletion workflows
cp get_vars.yml.example get_vars.yml        # Query workflows
cp update_vars_example.yml update_vars.yml  # Policy updates
```

### 2. Configure Connection Settings
```bash
# Edit CyberController connection details
nano vars/cc.yml
```
Add your CyberController IP, username, and password.

### 3. Verify Setup
```bash
# Test Ansible configuration
ansible-inventory --list
```

## 🚀 Quick Start (5 Minutes)

### Example: Create Network Classes
```bash
# 1. Configure your networks
nano vars/create_vars.yml  # Add device IPs and network definitions

# 2. Test with dry-run
ansible-playbook playbooks/create_network_class.yml --check

# 3. Execute
ansible-playbook playbooks/create_network_class.yml

# 4. Verify results
ansible-playbook playbooks/get_network_class.yml
```

## 📖 Complete Workflows

### 🌐 Network Class Workflows

#### Workflow 1: Create Network Classes
```bash
# 1. Configure your networks
nano vars/create_vars.yml

# 2. Test with dry-run
ansible-playbook playbooks/create_network_class.yml --check

# 3. Execute creation
ansible-playbook playbooks/create_network_class.yml
```

#### Workflow 2: Edit Network Classes  
```bash
# 1. View current configuration
ansible-playbook playbooks/get_network_class.yml

# 2. Define changes
nano vars/edit_vars.yml

# 3. Test changes
ansible-playbook playbooks/edit_network_class.yml --check

# 4. Apply changes
ansible-playbook playbooks/edit_network_class.yml
```

#### Workflow 3: Delete Network Classes
```bash
# 1. Identify targets for deletion
ansible-playbook playbooks/get_network_class.yml

# 2. Configure deletions
nano vars/delete_vars.yml

# 3. Test deletion plan
ansible-playbook playbooks/delete_network_class.yml --check

# 4. Execute deletions
ansible-playbook playbooks/delete_network_class.yml
```

#### Workflow 4: Query Network Classes
```bash
# Show all network classes
ansible-playbook playbooks/get_network_class.yml

# Filter specific classes (edit get_vars.yml first)
nano vars/get_vars.yml  # Set filter_class_names: ["class1", "class2"]
ansible-playbook playbooks/get_network_class.yml
```

### 🔒 Connection Limit Profile Workflows

#### Workflow 5: Create Connection Limit Profiles
```bash
# 1. Configure protections and profiles
nano vars/create_vars.yml

# 2. Test configuration
ansible-playbook playbooks/create_cl_profiles.yml --check

# 3. Create profiles
ansible-playbook playbooks/create_cl_profiles.yml
```

**Variation 5a: Create Protections Only**
```bash
# Define cl_protections section only, skip cl_profiles
nano vars/create_vars.yml
ansible-playbook playbooks/create_cl_profiles.yml
```

**Variation 5b: Create Profiles with Existing Protections**
```bash
# Skip cl_protections, define cl_profiles with existing protection names
nano vars/create_vars.yml
ansible-playbook playbooks/create_cl_profiles.yml
```

#### Workflow 6: Edit Connection Limit Protections
```bash
# 1. Configure changes (specify protection_index and parameters to change)
nano vars/edit_vars.yml

# 2. Preview changes
ansible-playbook playbooks/edit_cl_protections.yml --check

# 3. Apply changes
ansible-playbook playbooks/edit_cl_protections.yml
```

#### Workflow 7: Query Connection Limit Profiles
```bash
# Show all profiles and protections
ansible-playbook playbooks/get_cl_profiles.yml

# Filter specific profiles (edit get_vars.yml first)
nano vars/get_vars.yml  # Set filter_cl_profile_names: ["profile1"]
ansible-playbook playbooks/get_cl_profiles.yml
```

#### Workflow 8: Delete Connection Limit Profiles
```bash
# 1. Plan deletions
nano vars/delete_vars.yml

# 2. Preview deletion plan
ansible-playbook playbooks/delete_cl_profiles.yml --check

# 3. Execute deletions
ansible-playbook playbooks/delete_cl_profiles.yml
```

**Important Rules for Deletion**:
- **Profile deletions**: Remove protections from profiles (profile auto-deleted when last protection removed)
- **Protection deletions**: Delete protections entirely (protection must not be in any profile)
- **Order matters**: Profile deletions are processed before protection deletions
- **Dependencies**: Cannot delete protection if it's still associated with any profile

### 🛡️ Security Profile Workflows

#### Workflow 9: BDoS Profile Management
```bash
# Create BDoS profiles
nano vars/create_vars.yml
ansible-playbook playbooks/create_bdos_profile.yml --check
ansible-playbook playbooks/create_bdos_profile.yml

# Edit BDoS profiles
nano vars/edit_vars.yml
ansible-playbook playbooks/edit_bdos_profile.yml --check
ansible-playbook playbooks/edit_bdos_profile.yml

# Query BDoS profiles
ansible-playbook playbooks/get_bdos_profile.yml

# Delete BDoS profiles
nano vars/delete_vars.yml
ansible-playbook playbooks/delete_bdos_profile.yml --check
ansible-playbook playbooks/delete_bdos_profile.yml
```

#### Workflow 10: DNS Profile Management
```bash
# Create DNS profiles
nano vars/create_vars.yml
ansible-playbook playbooks/create_dns_profile.yml --check
ansible-playbook playbooks/create_dns_profile.yml

# Edit DNS profiles
nano vars/edit_vars.yml
ansible-playbook playbooks/edit_dns_profile.yml --check
ansible-playbook playbooks/edit_dns_profile.yml

# Query DNS profiles
ansible-playbook playbooks/get_dns_profile.yml

# Delete DNS profiles
nano vars/delete_vars.yml
ansible-playbook playbooks/delete_dns_profile.yml --check
ansible-playbook playbooks/delete_dns_profile.yml
```

#### Workflow 11: HTTPS Profile Management
```bash
# Create HTTPS profiles
nano vars/create_vars.yml
ansible-playbook playbooks/create_https_profile.yml --check
ansible-playbook playbooks/create_https_profile.yml

# Edit HTTPS profiles
nano vars/edit_vars.yml
ansible-playbook playbooks/edit_https_profile.yml --check
ansible-playbook playbooks/edit_https_profile.yml

# Query HTTPS profiles
ansible-playbook playbooks/get_https_profile.yml

# Delete HTTPS profiles
nano vars/delete_vars.yml
ansible-playbook playbooks/delete_https_profile.yml --check
ansible-playbook playbooks/delete_https_profile.yml
```

#### Workflow 12: Out-of-State (OOS) Profile Management
```bash
# Create OOS profiles
nano vars/create_vars.yml
ansible-playbook playbooks/create_oos_profile.yml --check
ansible-playbook playbooks/create_oos_profile.yml

# Edit OOS profiles
nano vars/edit_vars.yml
ansible-playbook playbooks/edit_oos_profile.yml --check
ansible-playbook playbooks/edit_oos_profile.yml

# Query OOS profiles
ansible-playbook playbooks/get_oos_profile.yml

# Delete OOS profiles
nano vars/delete_vars.yml
ansible-playbook playbooks/delete_oos_profile.yml --check
ansible-playbook playbooks/delete_oos_profile.yml
```

#### Workflow 13: Traffic Filter Management
```bash
# Create Traffic Filter profiles
nano vars/create_vars.yml
ansible-playbook playbooks/create_traffic_filter.yml --check
ansible-playbook playbooks/create_traffic_filter.yml

# Edit Traffic Filter profiles
nano vars/edit_vars.yml
ansible-playbook playbooks/edit_traffic_filter.yml --check
ansible-playbook playbooks/edit_traffic_filter.yml

# Query Traffic Filter profiles
ansible-playbook playbooks/get_traffic_filter.yml

# Delete Traffic Filter profiles
nano vars/delete_vars.yml
ansible-playbook playbooks/delete_traffic_filter.yml --check
ansible-playbook playbooks/delete_traffic_filter.yml
```

### 🔐 SSL Object Workflows

#### Workflow 14: SSL Object Management
```bash
# Create SSL objects
nano vars/create_vars.yml
ansible-playbook playbooks/create_ssl_object.yml --check
ansible-playbook playbooks/create_ssl_object.yml

# Edit SSL objects
nano vars/edit_vars.yml
ansible-playbook playbooks/edit_ssl_object.yml --check
ansible-playbook playbooks/edit_ssl_object.yml

# Query SSL objects
ansible-playbook playbooks/get_ssl_object.yml

# Delete SSL objects
nano vars/delete_vars.yml
ansible-playbook playbooks/delete_ssl_object.yml --check
ansible-playbook playbooks/delete_ssl_object.yml
```

### 🎯 Security Policy & Orchestration Workflows

#### Workflow 15: Complete Security Configuration (Orchestrated)
```bash
# 1. Configure comprehensive security setup
nano vars/create_vars.yml

# Configure orchestration flags
security_policy_config:
  create_network_classes: true
  create_cl_profiles: true
  create_bdos_profiles: true
  create_dns_profiles: true
  create_https_profiles: true
  create_oos_profiles: true
  create_traffic_filter_profiles: true
  create_ssl_objects: true
  create_security_policies: true
  apply_policies_after_creation: true

# 2. Preview full orchestration
ansible-playbook playbooks/create_full_config.yml --check

# 3. Execute complete configuration
ansible-playbook playbooks/create_full_config.yml
```

#### Workflow 16: Security Policy Management
```bash
# Edit existing security policies
nano vars/edit_vars.yml
ansible-playbook playbooks/edit_security_policy.yml --check
ansible-playbook playbooks/edit_security_policy.yml

# Query security policies and profiles
ansible-playbook playbooks/get_security_policy.yml

# Delete security policies
nano vars/delete_vars.yml
ansible-playbook playbooks/delete_security_policy.yml --check
ansible-playbook playbooks/delete_security_policy.yml
```

#### Workflow 17: Policy Updates
```bash
# Manual policy updates
nano vars/update_vars.yml  # Configure target devices
ansible-playbook playbooks/update_policies.yml

# Or specify devices directly
ansible-playbook playbooks/update_policies.yml -e "target_devices=['10.105.192.32','10.105.192.33']"
```

## ⚙️ Configuration Reference

### Device and Connection Configuration

#### Target Devices (`vars/*.yml`)
```yaml
# Define target DefensePro devices
dp_ip:
  - "10.105.192.32"
  - "10.105.192.33"
```

#### CyberController Connection (`vars/cc.yml`)
```yaml
cc_ip: "10.105.193.3"
username: "your_username"
password: "your_password"
log_level: "info"  # Options: info, debug, disabled
```

### Variable File Examples

#### Network Classes (`vars/create_vars.yml`)
```yaml
netclasses:
  - name: "web_servers"
    groups:
      - { address: "192.168.1.0", mask: "255.255.255.0" }
      - { address: "192.168.2.0", mask: "24" }  # CIDR notation also supported
```

#### Connection Limit Profiles (`vars/create_vars.yml`)
```yaml
# Protection subprofiles (optional)
cl_protections:
  - name: "web_protection"
    protocol: "tcp"
    threshold: "100"
    app_port_group: "https"
    tracking_type: "src_ip"
    action: "drop"
    packet_report: "enable"

# Profiles (optional)
cl_profiles:
  - name: "web_limits"
    protections:
      - "web_protection"
      - "existing_protection"  # Can reference existing protections
```

#### Security Policy Orchestration (`vars/create_vars.yml`)
```yaml
# Control orchestration behavior
security_policy_config:
  create_network_classes: true
  create_cl_profiles: true
  create_bdos_profiles: true
  create_dns_profiles: true
  create_https_profiles: true
  create_oos_profiles: true
  create_traffic_filter_profiles: true
  create_ssl_objects: true
  create_security_policies: true
  apply_policies_after_creation: true

# Security policies with profile bindings
create_security_policies:
  - policy_name: "comprehensive_policy"
    state: "enable"
    action: "report_only"
    priority: "700"
    src_network: "any"
    dst_network: "web_servers"
    direction: "oneway"
    
    # Profile bindings (all optional)
    connection_limit_profile: "web_limits"
    bdos_profile: "bdos_profile_1"
    dns_flood_profile: "dns_profile_1"
    https_flood_profile: "https_profile_1"
    traffic_filters_profile: "tf_profile_1"
    signature_protection_profile: "All-DoS-Shield"
```

## 🛠️ Best Practices

### Development Workflow
1. **Always test first**: Use `--check` flag for dry-run validation
2. **Start small**: Begin with single device, expand to multiple devices
3. **Use filtering**: Leverage `filter_*_names` in get operations for focused results
4. **Incremental changes**: Edit only parameters you need to change
5. **Backup configurations**: Query current state before making changes

### Error Handling
- **Check mode validation**: Preview shows exactly what will be changed
- **Dependency validation**: Profile deletions validate dependencies
- **Error collection**: Batch operations collect and report all errors
- **Device locking**: Automatic device locking prevents configuration conflicts

### Common Patterns
- **Create-then-query**: Verify results after creation operations
- **Edit-specific-parameters**: Only specify parameters you want to change
- **Conditional orchestration**: Use security_policy_config flags to control stages
- **Profile references**: Mix new and existing profiles in security policies

## 📞 Support & Troubleshooting

### Common Issues
1. **Connection errors**: Verify CyberController IP, credentials, and network connectivity
2. **Parameter validation**: Check parameter formats and valid values in examples
3. **Profile dependencies**: Ensure profiles exist before referencing in policies
4. **Device locking**: Wait for lock release if device is locked by another process

### Getting Help
- **Configuration examples**: All `*.example` files contain detailed parameter documentation
- **Technical details**: See [DEVELOPER.md](DEVELOPER.md) for API documentation and architecture
- **Error messages**: Most error messages include specific guidance for resolution