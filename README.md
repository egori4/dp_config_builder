# DefensePro Configuration Builder

Ansible automation for Radware DefensePro security configuration management.

Automate configuration of DefensePro security profiles, policies, and network settings across multiple devices using Ansible playbooks and custom modules.

## Quick Start

**For Operators/Users**: See [USER_GUIDE.md](USER_GUIDE.md) for step-by-step instructions

**For Developers**: See [DEVELOPER.md](DEVELOPER.md) for technical architecture and API details

## Prerequisites

Before using the DefensePro Configuration Builder, you need to set up the basic Ansible environment:

### 1. Create Ansible Configuration
```bash
# Copy the example Ansible configuration
cp ansible_example.cfg ansible.cfg

# Edit if needed (default settings work for most cases)
nano ansible.cfg
```

### 2. Create Inventory File  
```bash
# Copy the example inventory
cp inventory_example.ini inventory.ini

# Edit the inventory (usually no changes needed)
nano inventory.ini
```

### 3. Setup Variable Files
```bash
# Copy configuration templates
cd vars/
cp cc_example.yml cc.yml                    # CyberController connection settings
cp create_vars.yml.example create_vars.yml  # For creating resources  
cp edit_vars.yml.example edit_vars.yml      # For editing resources
cp delete_vars.yml.example delete_vars.yml  # For deleting resources
cp get_vars.yml.example get_vars.yml        # For querying resources
cp update_vars_example.yml update_vars.yml  # For policy updates

# Edit connection settings
nano cc.yml  # Add your CyberController IP, username, password

# Edit other vars files referenced above as needed
```

### 4. Verify Setup
```bash

# Test inventory configuration  
ansible-inventory --list

## Repository Structure

```
dp_config_builder/
├── README.md                 # Project overview and quick start
├── USER_GUIDE.md            # Step-by-step user instructions  
├── DEVELOPER.md             # Technical documentation for developers
├── 
├── ansible.cfg              # Ansible configuration (create from ansible_example.cfg)
├── ansible_example.cfg      # Template for Ansible configuration
├── inventory.ini            # Ansible inventory (create from inventory_example.ini)
├── inventory_example.ini    # Template for Ansible inventory
├── 
├── playbooks/               # Ansible playbooks for automation
│   ├── create_*.yml         # Creation playbooks
│   ├── edit_*.yml           # Editing playbooks  
│   ├── delete_*.yml         # Deletion playbooks
│   ├── get_*.yml            # Query/retrieval playbooks
│   ├── log/                 # Execution logs (auto-created)
│   └── tmp/                 # Temporary files (auto-created)
├── 
├── plugins/                 # Custom Ansible modules and utilities
│   ├── modules/             # Custom modules 
│   │   ├── create_*.py      # Creation modules
│   │   ├── edit_*.py        # Editing modules
│   │   ├── delete_*.py      # Deletion modules
│   │   ├── get_*.py         # Query modules
│   │   └── dp_*.py          # Device lock/unlock utilities
│   └── module_utils/        # Shared utilities
│       ├── radware_cc.py    # HTTP client with session management
│       └── logger.py        # Structured logging utility
├── 
├── vars/                    # Configuration files and templates
│   ├── cc.yml               # CyberController connection (create from cc_example.yml)
│   ├── cc_example.yml       # Template for CC connection settings
│   ├── *_vars.yml          # Your configuration files (git-ignored)
│   └── *_vars.yml.example  # Safe templates (in git)
└── 
└── tasks/                   # Reusable task fragments (advanced usage)
    └── cl_profile_tasks/    # Connection limit profile task components
```

## What This Does

- Create, edit, delete, and query DefensePro security profile and policy configurations
- Manage multiple DefensePro devices simultaneously

## Available Operations

### Network Class Management

| Playbook | Purpose | Documentation |
|----------|---------|---------------|
| `create_network_class.yml` | Create new network classes | [USER_GUIDE.md](USER_GUIDE.md#workflow-1-create-new-network-classes) |
| `edit_network_class.yml` | Modify existing networks | [USER_GUIDE.md](USER_GUIDE.md#workflow-2-modify-existing-networks) |
| `delete_network_class.yml` | Remove network groups | [USER_GUIDE.md](USER_GUIDE.md#workflow-3-clean-up-networks) |
| `get_network_class.yml` | Query current state with filtering | [USER_GUIDE.md](USER_GUIDE.md#workflow-6-get-network-classes-with-filtering) |

### Connection Limit Profiles

| Playbook | Purpose | Documentation |
|----------|---------|---------------|
| `create_cl_profiles.yml` | Create connection limit profiles and protections | *See create_vars.yml for configuration* |
| `edit_cl_protections.yml` | Edit existing connection limit protections | *See edit_vars.yml for configuration* |
| `get_cl_profiles.yml` | Get connection limit profiles and protections (with optional filtering) | *See get_vars.yml for configuration* |
| `delete_cl_profiles.yml` | Delete connection limit profiles and protections (flexible removal) | *See delete_vars.yml for configuration* |

**Connection Limit Protection Features**:
-  **8 configurable parameters** (protocol, threshold, app_port_group, tracking_type, action, packet_report, protection_type, index)
-  **Flexible creation**: All parameters optional except name (sensible defaults provided)
-  **Optional sections**: Both `cl_protections` and `cl_profiles` sections are optional
-  **Partial editing**: Only specify parameters you want to change
-  **Profile querying**: Get all profiles and protections with optional filtering by profile names
-  **Flexible deletion**: Remove protections from profiles OR delete protections entirely
-  **Index control**: Optional index parameter (0 or 450001+, defaults to 0)
-  **Profile management**: Reference existing or newly created protections

### OOS Profile Management

| Playbook | Purpose | Documentation |
|----------|---------|---------------|
| `create_oos_profile.yml` | Create new OOS profile        | [USER\_GUIDE.md](USER_GUIDE.md#workflow-11-create-oos-profile)  |
| `edit_oos_profile.yml`   | Modify existing OOS Profile   | [USER\_GUIDE.md](USER_GUIDE.md#workflow-11a-edit-oos-profile)   |
| `delete_oos_profile.yml` | Remove OOS profile            | [USER\_GUIDE.md](USER_GUIDE.md#workflow-11b-delete-oos-profile) |
| `get_oos_profile.yml`    | Query current OOS Profile     | [USER\_GUIDE.md](USER_GUIDE.md#workflow-11c-get-oos-profile)    |


### BDoS Profile Management
| Playbook | Purpose | Documentation |
|----------|---------|---------------|
| `create_bdos_profile.yml` | Create new BDoS flood profiles           | [USER\_GUIDE.md](USER_GUIDE.md#workflow-9-create-bdos-profiles)             |
| `edit_bdos_profile.yml`   | Modify existing BDoS profiles            | [USER\_GUIDE.md](USER_GUIDE.md#workflow-9a-edit-bdos-profiles)               |
| `delete_bdos_profile.yml` | Remove BDoS profiles                     | [USER\_GUIDE.md](USER_GUIDE.md#workflow-9b-delete-bdos-profiles)             |
| `get_bdos_profile.yml`    | Query current BDoS profile configuration | [USER\_GUIDE.md](USER_GUIDE.md#workflow-9c-get-bdos-profiles-with-filtering) |

### DNS Profile Management
| Playbook | Purpose | Documentation |
|----------|---------|---------------|
| `create_dns_profile.yml` | Create new dns flood profiles           | [USER\_GUIDE.md](USER_GUIDE.md#workflow-10-create-dns-profile)             |
| `edit_dns_profile.yml`   | Modify existing dns profiles            | [USER\_GUIDE.md](USER_GUIDE.md#workflow-10a-edit-dns-profile)               |
| `delete_dns_profile.yml` | Remove dns profiles                     | [USER\_GUIDE.md](USER_GUIDE.md#workflow-10b-delete-dns-profile)             |
| `get_dns_profile.yml`    | Query current dns profile configuration | [USER\_GUIDE.md](USER_GUIDE.md#workflow-10c-get-dns-profile) |

### SSL Object Management
| Playbook | Purpose | Documentation |
|----------|---------|---------------|
| `create_ssl_object.yml` | Create new SSL object(s)      | [USER\_GUIDE.md](USER_GUIDE.md#workflow-ssl-create) |
| `edit_ssl_object.yml`   | Modify existing SSL object(s) | [USER\_GUIDE.md](USER_GUIDE.md#workflow-ssl-edit)   |
| `delete_ssl_object.yml` | Remove SSL object(s)          | [USER\_GUIDE.md](USER_GUIDE.md#workflow-ssl-delete) |
| `get_ssl_object.yml`    | Query current SSL object(s)   | [USER\_GUIDE.md](USER_GUIDE.md#workflow-ssl-get)    |

### HTTPS Profile Management

| Playbook | Purpose | Documentation |
|----------|---------|---------------|
| `create_https_profile.yml` | Create new HTTPS profile        | [USER_GUIDE.md](USER_GUIDE.md#workflow-create-https-profile)  |
| `edit_https_profile.yml`   | Modify existing HTTPS profile   | [USER_GUIDE.md](USER_GUIDE.md#workflow-edit-https-profile)    |
| `delete_https_profile.yml` | Remove HTTPS profile            | [USER_GUIDE.md](USER_GUIDE.md#workflow-delete-https-profile)  |
| `get_https_profile.yml`    | Query current HTTPS profile     | [USER_GUIDE.md](USER_GUIDE.md#workflow-get-https-profile)     |

### Traffic Filter Management

| Playbook | Purpose | Documentation |
|----------|---------|---------------|
| `create_traffic_filter.yml` | Create new Traffic Filter       | [USER_GUIDE.md](USER_GUIDE.md#workflow-create-traffic-filter)  |
| `edit_traffic_filter.yml`   | Modify existing Traffic Filter   | [USER_GUIDE.md](USER_GUIDE.md#workflow-edit-traffic-filter)    |
| `delete_traffic_filter.yml` | Remove Traffic Filter            | [USER_GUIDE.md](USER_GUIDE.md#workflow-delete-traffic-filter)  |
| `get_traffic_filter.yml`    | Query current Traffic Filter     | [USER_GUIDE.md](USER_GUIDE.md#workflow-get-traffic-filter)     |

### SYN Profile Management
| Playbook | Purpose | Documentation |
|----------|---------|---------------|
| `create_syn_profiles.yml`  | Create new SYN flood profiles           | [USER\_GUIDE.md](USER_GUIDE.md#workflow-11-create-syn-profile)    |
| `edit_syn_protections.yml` | Modify existing SYN protections         | [USER\_GUIDE.md](USER_GUIDE.md#workflow-11a-edit-syn-protections) |
| `delete_syn_profiles.yml`  | Remove SYN profiles and/or protections  | [USER\_GUIDE.md](USER_GUIDE.md#workflow-11b-delete-syn-profiles)  |
| `get_syn_profiles.yml`     | Query current SYN profile configuration | [USER\_GUIDE.md](USER_GUIDE.md#workflow-11c-get-syn-profiles)     |


### Security Policy Management

| Playbook | Purpose | Documentation |
|----------|---------|---------------|
| `create_full_config.yml` | **ORCHESTRATOR**: Create security policies with profile bindings | [USER_GUIDE.md](USER_GUIDE.md#workflow-12-create-security-policies-with-profile-bindings) |
| `edit_security_policy.yml` | Edit existing security policies (partial updates and profile management) | [USER_GUIDE.md](USER_GUIDE.md#editing-security-policies) |
| `delete_security_policy.yml` | Delete security policies with optional profile cleanup | [USER_GUIDE.md](USER_GUIDE.md#deleting-security-policies) |
| `update_policies.yml` | Apply DefensePro configuration updates (policy updates) | [USER_GUIDE.md](USER_GUIDE.md#workflow-11-apply-defensepro-policy-updates) |

**Security Policy Features**:
- **Unified orchestration**: Single playbook creates profiles and security policies
- **Policy editing**: Modify existing policies with partial updates and profile management
- **Policy deletion**: Remove policies with dual deletion modes (policy-only vs policy+profiles)
- **Profile binding**: Bind different protection profile types to security policies
- **Profile management**: Attach/detach profiles using names or empty strings
- **Flexible control**: Individual control flags for each creation stage
- **Conditional execution**: Centralized device locking and policy updates during orchestration
- **Minimal parameters**: Only policy name required - DefensePro provides sensible defaults
- **Partial updates**: For editing, only specify parameters to change - others remain unchanged
- **Safe deletion**: Default policy-only deletion preserves profiles for other policies
- **Advanced cleanup**: Optional policy+profiles deletion for comprehensive cleanup
- **Comprehensive configuration**: Full policy parameters when needed (source, destination, direction, priority, actions)
- **Error handling**: Detailed error reporting and validation
- **Preview mode**: Check mode support to preview planned operations
- **Existing profile support**: Use existing profiles without recreating them

**Section Optionality**:
- **Protections only**: Define `cl_protections`, skip `cl_profiles`
- **Profiles only**: Skip `cl_protections`, use existing protection names in `cl_profiles`
- **Both sections**: Create new protections and profiles together

**Parameter Status**:
- **MANDATORY**: `name` (create), `protection_index` (edit)
- **OPTIONAL**: All other parameters have defaults and can be omitted



## Documentation by Audience

### I'm an Operator/User
- **Goal**: Get things done quickly and safely
- **Read**: [USER_GUIDE.md](USER_GUIDE.md)
- **Includes**: Setup, workflows, troubleshooting, best practices

### I'm a Developer
- **Goal**: Understand architecture, extend functionality
- **Read**: [DEVELOPER.md](DEVELOPER.md)
- **Includes**: API references, module patterns, testing, contributing

## Super Quick Example

**Note**: Complete the [Prerequisites](#prerequisites) first, then:

```bash
# Network Classes Example
cd vars/
cp create_vars.yml.example create_vars.yml
```
# Edit create_vars.yml with your networks and devices
ansible-playbook playbooks/create_network_class.yml

# Connection Limit Profiles Example
ansible-playbook playbooks/create_cl_profiles.yml

# Edit Connection Limit Protections (uses edit_cl_configuration module)
ansible-playbook playbooks/edit_cl_protections.yml

# Get Connection Limit Profiles (uses get_cl_configuration module)
ansible-playbook playbooks/get_cl_profiles.yml

# Delete Connection Limit Profiles (uses delete_cl_configuration module)
ansible-playbook playbooks/delete_cl_profiles.yml

# Create BDoS Profile
ansible-playbook playbooks/create_bdos_profile.yml

# Edit BDoS Profile (uses edit_bdos_profile module)
ansible-playbook playbooks/edit_bdos_profile.yml

# Get BDoS Profile (uses get_bdos_profile module)
ansible-playbook playbooks/get_bdos_profile.yml

# Delete BDoS Profile (uses delete_bdos_profile module)
ansible-playbook playbooks/delete_bdos_profile.yml

# Get all DNS profiles from devices
ansible-playbook playbooks/get_dns_profile.yml

# Create new DNS profiles
ansible-playbook playbooks/create_dns_profile.yml

# Edit existing DNS profiles
ansible-playbook playbooks/edit_dns_profile.yml

# Delete DNS profiles
ansible-playbook playbooks/delete_dns_profile.yml

# Get all OOS profiles from devices
ansible-playbook playbooks/get_oos_profile.yml

# Create new OOS profiles
ansible-playbook playbooks/create_oos_profile.yml

# Edit existing OOS profiles
ansible-playbook playbooks/edit_oos_profile.yml

# Delete OOS profiles
ansible-playbook playbooks/delete_oos_profile.yml

# Get all SSL objects from devices
ansible-playbook playbooks/get_ssl_object.yml

# Create new SSL objects
ansible-playbook playbooks/create_ssl_object.yml

# Edit existing SSL objects
ansible-playbook playbooks/edit_ssl_object.yml

# Delete SSL objects
ansible-playbook playbooks/delete_ssl_object.yml

# Get all HTTPS profiles from devices
ansible-playbook playbooks/get_https_profile.yml

# Create new HTTPS profiles
ansible-playbook playbooks/create_https_profile.yml

# Edit existing HTTPS profiles
ansible-playbook playbooks/edit_https_profile.yml

# Delete HTTPS profiles
ansible-playbook playbooks/delete_https_profile.yml

# Get all Traffic Filter from devices
ansible-playbook playbooks/get_traffic_filter.yml

# Create new Traffic Filter
ansible-playbook playbooks/create_traffic_filter.yml

# Edit existing Traffic Filter
ansible-playbook playbooks/edit_traffic_filter.yml

# Delete Traffic Filter
ansible-playbook playbooks/delete_traffic_filter.yml

# Security Policy Creation (using vars/create_vars.yml configuration)
ansible-playbook playbooks/create_full_config.yml

# Security Policy Editing (using vars/edit_vars.yml configuration)  
ansible-playbook playbooks/edit_security_policy.yml

# Security Policy Deletion (using vars/delete_vars.yml configuration)
ansible-playbook playbooks/delete_security_policy.yml



## Version History

| Version | Date | Changes |
|---------|------|---------|
| v0.2.0 | 2025-09-12 | Added security policy orchestration with profile binding capabilities
<br>• Added update policies playbook
<br>• Enhanced Policy creation module logic, effectiveness holistically
<br>• Added conditional Update policies and conditional lock/unlock when creating profiles/policies
<br>• Updated create security module to send only parameters defined by user
<br>• Added summary log after creating connection limit profile
<br>• Optimized/standardized the format of update policies playbook |
| v0.1.10 | 2025-09-30 | Added Protected Traffic Filter functionality |
| v0.1.9 | 2025-09-26 | Added Protected SSL Object functionality |
| v0.1.8 | 2025-09-24 | Added SYN Flood functionality |
| v0.1.6 | 2025-09-22 | Added DNS Flood functionality |
| v0.1.5 | 2025-09-18 | Added OOS functionality |
| v0.1.4.1 | 2025-09-10 | Updated documentation- added prerequisites and detailed directories structure, architecture
| v0.1.4 | 2025-08-29 | Added functionality - crate/edit/get/delete connection limit profiles and protections |
| v0.1.3 |  2025-09-19 | Added BDOS functionality|
| v0.1.2.1 | 2025-09-08 | Enhanced network classes configuraion - simplified architecture, logging and debugging enhancments, added preview |
| v0.1.2 | 2025-08-28 | Added edit functionality for network classes, improved variable management, aligned configuration, added documentation |
| v0.1.1 | 2025-08-19 | Enhanced logging, session management |
| v0.1.0 | 2025-08-19 | Initial release with network class create/edit/delete/get operations |

## Getting Help

1. Quick Issues: Check [USER_GUIDE.md troubleshooting](USER_GUIDE.md#troubleshooting)
2. Technical Issues: See [DEVELOPER.md](DEVELOPER.md)
3. Examples: All `.example` files have detailed comments

## Maintainer & Contact

**Project Maintainer**: [Egor Egorov]  
**Email**: [egore@radware.com]  
**GitHub Radware**: [@rdwr-egore](https://github.com/rdwr-egore)
**GitHub Private**: [@egori4](https://github.com/egori4)

**Contributor**:  [@rahulku25](https://github.com/rahulku25)