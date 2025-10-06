# DefensePro Configuration Builder

**Ansible automation for Radware DefensePro security configuration management**

Automate creation, editing, deletion, and querying of DefensePro security profiles, policies, and network settings across multiple devices using Ansible playbooks and custom modules.

## 🚀 Quick Start

- **👥 For Users/Operators**: See [USER_GUIDE.md](USER_GUIDE.md) for step-by-step workflows and examples
- **🔧 For Developers**: See [DEVELOPER.md](DEVELOPER.md) for technical architecture and API documentation

## 📋 Prerequisites

Complete these setup steps before using any playbooks:

### 1. Create Configuration Files
```bash
# Copy Ansible configuration templates
cp ansible_example.cfg ansible.cfg
cp inventory_example.ini inventory.ini

# Copy variable templates
cd vars/
cp cc_example.yml cc.yml                    # CyberController connection settings
cp create_vars.yml.example create_vars.yml  # Creation variables
cp edit_vars.yml.example edit_vars.yml      # Editing variables
cp delete_vars.yml.example delete_vars.yml  # Deletion variables
cp get_vars.yml.example get_vars.yml        # Query variables
cp update_vars_example.yml update_vars.yml  # Policy update variables
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

## 🎯 What This Automates

### Core DefensePro Management
- **Network Classes**: Create, edit, delete, and query network classifications
- **Security Profiles**: Manage Connection Limit, BDoS, DNS, HTTPS, OOS, SSL Objects, Traffic Filter profiles
- **Security Policies**: Orchestrated policy creation with profile bindings
- **Device Management**: Automated locking, configuration, and policy updates

### Key Features
- **Multi-device support**: Configure multiple DefensePro devices simultaneously
- **Conditional execution**: Enable/disable specific configuration stages
- **Preview mode**: Dry-run support with `--check` flag
- **Error handling**: Comprehensive error collection and reporting
- **Partial updates**: Edit only specified parameters, leave others unchanged
- **Profile orchestration**: Unified workflow for profiles and policy creation

## 📁 Repository Structure

```
dp_config_builder/
├── 📚 Documentation
│   ├── README.md              # Project overview (this file)
│   ├── USER_GUIDE.md          # Step-by-step workflows for operators
│   └── DEVELOPER.md           # Technical architecture for developers
├── 
├── ⚙️ Configuration
│   ├── ansible.cfg            # Ansible runtime settings
│   ├── inventory.ini          # Ansible hosts configuration  
│   └── vars/                  # Variable files and templates
│       ├── cc.yml             # CyberController connection (your settings)
│       ├── *_vars.yml         # Your configuration files
│       └── *.example          # Safe templates for copying
├── 
├── 🎭 Automation
│   ├── playbooks/             # Ansible playbooks for operations
│   │   ├── create_*.yml       # Creation workflows
│   │   ├── edit_*.yml         # Editing workflows
│   │   ├── delete_*.yml       # Deletion workflows
│   │   └── get_*.yml          # Query workflows
│   └── plugins/               # Custom modules and utilities
│       ├── modules/           # DefensePro automation modules
│       └── module_utils/      # Shared utilities (HTTP client, logging)
└── 
└── 🔍 Runtime Data (auto-created)
    ├── log/                   # Execution logs
    └── tmp/                   # Session cache and temporary files
```

## 🛠️ Available Operations

### Network Classes
- **Create**: `create_network_class.yml` - Define network classifications and IP ranges
- **Edit**: `edit_network_class.yml` - Modify existing network groups
- **Delete**: `delete_network_class.yml` - Remove network classifications
- **Query**: `get_network_class.yml` - Retrieve current network class configurations

### Security Profiles

| Profile Type | Create | Edit | Delete | Query |
|--------------|--------|------|--------|-------|
| **Connection Limit** | `create_cl_profiles.yml` | `edit_cl_protections.yml` | `delete_cl_profiles.yml` | `get_cl_profiles.yml` |
| **BDoS Flood** | `create_bdos_profile.yml` | `edit_bdos_profile.yml` | `delete_bdos_profile.yml` | `get_bdos_profile.yml` |
| **DNS Protection** | `create_dns_profile.yml` | `edit_dns_profile.yml` | `delete_dns_profile.yml` | `get_dns_profile.yml` |
| **HTTPS Flood** | `create_https_profile.yml` | `edit_https_profile.yml` | `delete_https_profile.yml` | `get_https_profile.yml` |
| **Out-of-State** | `create_oos_profile.yml` | `edit_oos_profile.yml` | `delete_oos_profile.yml` | `get_oos_profile.yml` |
| **Traffic Filter** | `create_traffic_filter.yml` | `edit_traffic_filter.yml` | `delete_traffic_filter.yml` | `get_traffic_filter.yml` |

### SSL Objects
- **Create**: `create_ssl_object.yml` - Configure SSL termination and inspection
- **Edit**: `edit_ssl_object.yml` - Modify SSL object settings
- **Delete**: `delete_ssl_object.yml` - Remove SSL objects
- **Query**: `get_ssl_object.yml` - Retrieve SSL object configurations

### Security Policies & Orchestration
- **🎯 Full Orchestration**: `create_full_config.yml` - Create profiles and policies with bindings
- **Edit Policies**: `edit_security_policy.yml` - Modify existing security policies
- **Delete Policies**: `delete_security_policy.yml` - Remove policies (with optional profile cleanup)
- **Update Policies**: `update_policies.yml` - Apply configuration changes to devices

## 📚 Documentation Guide

### For Different Users

| I am a... | I want to... | Read this... |
|-----------|--------------|--------------|
| **Operator/User** | Configure DefensePro devices, run workflows | [USER_GUIDE.md](USER_GUIDE.md) |
| **Developer** | Understand architecture, extend functionality | [DEVELOPER.md](DEVELOPER.md) |
| **New User** | Get started quickly | This README + [USER_GUIDE.md](USER_GUIDE.md) |

## 🏃 Quick Example

After completing [Prerequisites](#-prerequisites):

```bash
# 1. Configure your environment
nano vars/create_vars.yml  # Add your device IPs and desired configuration

# 2. Test with dry-run
ansible-playbook playbooks/create_network_class.yml --check

# 3. Execute
ansible-playbook playbooks/create_network_class.yml

# 4. Verify results  
ansible-playbook playbooks/get_network_class.yml
```

## 🔄 Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| **v0.2.1** | 2025-10-06 | Updated documentation- new format |
| **v0.2.0** | 2025-09-12 | Security policy orchestration, profile binding, policy updates |
| **v0.1.10** | 2025-09-30 | Traffic Filter profile management |
| **v0.1.9** | 2025-09-26 | SSL Object configuration |
| **v0.1.7** | 2025-09-24 | HTTPS Flood protection profiles |
| **v0.1.6** | 2025-09-22 | DNS Flood protection profiles |
| **v0.1.5** | 2025-09-18 | Out-of-State (OOS) profiles |
| **v0.1.4** | 2025-08-29 | Connection Limit profiles and protections |
| **v0.1.3** | 2025-09-19 | BDoS Flood protection profiles |
| **v0.1.2** | 2025-08-28 | Network class editing, improved variable management |
| **v0.1.0** | 2025-08-19 | Initial release with network class operations |

## 📞 Support & Maintenance

**Project Maintainer**: Egor Egorov ([@egori4](https://github.com/egori4))  
**Email**: egore@radware.com  
**Contributor**: [@rahulku25](https://github.com/rahulku25)
**Email**: RahulKu@radware.com

### Getting Help
1. **Quick Issues**: Check [USER_GUIDE.md](USER_GUIDE.md) troubleshooting section
2. **Technical Issues**: See [DEVELOPER.md](DEVELOPER.md) architecture documentation  
3. **Configuration Examples**: All `*.example` files contain detailed comments