# DefensePro Configuration Builder

Ansible automation for Radware DefensePro security configuration management.

Automate configuration of DefensePro security profiles, policies, and network settings across multiple devices using Ansible playbooks and custom modules.

## Quick Start

**For Operators/Users**: See [USER_GUIDE.md](USER_GUIDE.md) for step-by-step instructions

**For Developers**: See [DEVELOPER.md](DEVELOPER.md) for technical architecture and API details

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
| `get_network_class.yml` | Query current state | [USER_GUIDE.md](USER_GUIDE.md#common-workflows) |

### BDoS Profile Management

| Playbook | Purpose | Documentation |
                                                    
| `create_bdos_profile.yml` | Create new BDoS Flood profiles      | [USER\_GUIDE.md](USER_GUIDE.md#workflow-1-create-new-bdos-flood-profiles)      |
| `edit_bdos_profile.yml`   | Modify existing BDoS Flood profiles | [USER\_GUIDE.md](USER_GUIDE.md#workflow-2-modify-existing-bdos-flood-profiles) |
| `delete_bdos_profile.yml` | Remove BDoS Flood profiles          | [USER\_GUIDE.md](USER_GUIDE.md#workflow-3-clean-up-bdos-flood-profiles)        |
| `get_bdos_profile.yml`   | Query current BDoS Flood profiles   | [USER\_GUIDE.md](USER_GUIDE.md#common-workflows)                               |



## Repository Structure

```
dp_config_builder/
├── USER_GUIDE.md             # Start here for operations
├── DEVELOPER.md              # Technical documentation  
├── playbooks/                # Ansible playbooks
├── plugins/
│   ├── modules/              # Custom Ansible modules
│   └── module_utils/         # Shared utilities
└── vars/                     # Configuration templates
    ├── *.yml.example         # Safe templates (in Git)
    └── *.yml                 # Your configs (git-ignored)
```

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

```bash
# 1. Setup (one time)
cd vars/
cp create_vars.yml.example create_vars.yml
# Edit create_vars.yml with your networks and devices

# 2. Create network classes (example with current functionality)
ansible-playbook playbooks/create_network_class.yml
```

## Version History

| Version | Date | Changes |
|---------|------|---------|     |
| v0.1.3 | 2025-08-29 | Added BDoS functionality,create,edit,delete,get operation |
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
