# DefensePro Configuration Builder - Developer Guide

**Technical documentation for developers working on the DefensePro Ansible modules**

## Prerequisites for Development

Before working with the DefensePro Configuration Builder modules:

### Environment Setup
```bash
# 1. Ensure basic Ansible configuration exists
cp ansible_example.cfg ansible.cfg
cp inventory_example.ini inventory.ini

# 2. Set up connection configuration for testing
cd vars/
cp cc_example.yml cc.yml
# Edit cc.yml with test environment details


### Development Environment
```bash
# Install development dependencies
pip3 install ansible requests

# Verify Python module imports
python3 -c "
import sys
sys.path.append('./plugins/module_utils')
from radware_cc import RadwareCC
from logger import Logger
print('Module utils import successful')
"
```

## Architecture Overview

The DefensePro Configuration Builder follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERACTION LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│ ansible-playbook commands → Configuration Files (vars/)         │
└─────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│ Ansible Playbooks (playbooks/)                                  │
│ • Device iteration • Output formatting • Playbook-level errors  │
└─────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│ Custom Ansible Modules (plugins/modules/)                       │
│ • Parameter validation • Batch processing • State management    │
│ • Operation error handling • Error collection & aggregation     │
└─────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│ Utilities (plugins/module_utils/)                               │
│ • HTTP client • Session management • Logging                    │
└─────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SYSTEMS                            │
├─────────────────────────────────────────────────────────────────┤
│ Radware CyberController ←→ DefensePro Devices                   │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure Deep Dive

```
dp_config_builder/
├── 📁 Configuration Files
│   ├── ansible.cfg
│   ├── ansible_example.cfg
│   ├── inventory.ini
│   └── inventory_example.ini
├── 
├── 📁 Documentation  
│   ├── README.md                # Project overview and quick start
│   ├── USER_GUIDE.md           # Step-by-step operational guide
│   └── DEVELOPER.md            # Technical architecture (this file)
├── 
├── 📁 playbooks/               # ORCHESTRATION LAYER
│   ├── 🎯 Network Class Operations
│   │   ├── create_network_class.yml
│   │   ├── edit_network_class.yml
│   │   ├── delete_network_class.yml
│   │   └── get_network_class.yml
│   ├── 🎯 Connection Limit Operations
│   │   ├── create_cl_profiles.yml
│   │   ├── edit_cl_protections.yml
│   │   ├── get_cl_profiles.yml
│   │   └── delete_cl_profiles.yml
│   ├── 🎯 BDoS Operations
│   │   ├── create_bdos_profile.yml       # Create BDoS profiles
│   │   ├── edit_bdos_profile.yml         # Edit BDoS profiles (partial updates)
│   │   ├── get_bdos_profile.yml          # Query BDoS profiles
│   │   └── delete_bdos_profile.yml       # Delete BDoS profiles
│   ├── 🎯 DNS Flood Operations
│   │   ├── create_dns_profile.yml        # Create DNS flood profiles
│   │   ├── edit_dns_profile.yml          # Edit DNS flood profiles
│   │   ├── get_dns_profile.yml           # Query DNS flood profiles
│   │   └── delete_dns_profile.yml        # Delete DNS flood profiles
│   ├── 🎯 Security Policy Operations
│   │   ├── create_security_policy.yml
│   │   ├── edit_security_policy.yml
│   │   └── delete_security_policy.yml
│   ├── 📊 Runtime Data (auto-created)
│   │   ├── log/                        # Execution logs by date
│   │   │   └── log_YYYYMMDD.log       # Daily log files
│   │   └── tmp/                        # Temporary files  
│   │       └── radware_cc_sessions/    # Session cache files
├── 
├── 📁 plugins/
│   ├── 📁 modules/
│   │   ├── 🔧 Network Class Modules
│   │   │   ├── create_network_class.py
│   │   │   ├── edit_network_class.py
│   │   │   ├── delete_network_class.py
│   │   │   └── get_network_class.py
│   │   ├── 🔧 Connection Limit Modules
│   │   │   ├── create_cl_configuration.py
│   │   │   ├── edit_cl_configuration.py
│   │   │   ├── get_cl_configuration.py
│   │   │   └── delete_cl_configuration.py
│   │   ├── 🔧 BDoS Modules
│   │   │   ├── create_bdos_profile.py
│   │   │   ├── edit_bdos_profile.py
│   │   │   ├── get_bdos_profile.py
│   │   │   └── delete_bdos_profile.py
│   │   ├── 🔧 DNS Flood Modules
│   │   │   ├── create_dns_profile.py
│   │   │   ├── edit_dns_profile.py
│   │   │   ├── get_dns_profile.py
│   │   │   └── delete_dns_profile.py
│   │   ├── 🔧 Security Policy Modules
│   │   │   ├── create_security_policy.py
│   │   │   ├── edit_security_policy.py
│   │   │   └── delete_security_policy.py
│   │   └── 🔧 Device Management
│   │       ├── dp_lock.py
│   │       └── dp_unlock.py
│   └── 📁 module_utils/
│       ├── radware_cc.py
│       └── logger.py
├── 
├── 📁 vars/
│   ├── 🔗 Connection Configuration
│   │   ├── cc.yml
│   │   └── cc_example.yml
│   ├── 🎯 Operation Variables
│   │   ├── create_vars.yml
│   │   ├── edit_vars.yml
│   │   ├── delete_vars.yml
│   │   ├── get_vars.yml
│   │   └── update_vars.yml
│   └── 📋 Variable Templates
│       ├── create_vars.yml.example
│       ├── edit_vars.yml.example
│       ├── delete_vars.yml.example
│       ├── get_vars.yml.example
│       └── update_vars_example.yml
└──

```

### Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   vars/*.yml    │───▶│ playbooks/*.yml │───▶│ plugins/modules │
│   (Parameters)  │    │  (Orchestration)│    │ (Business Logic)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐             │
│ CyberController │◀───│module_utils/*.py│◀────────────┘
│   (DefensePro)  │    │ (Infrastructure)│
└─────────────────┘    └─────────────────┘
```

### Error Handling Distribution

| Layer | Error Handling Responsibilities | Examples |
|-------|--------------------------------|----------|
| **Orchestration** | Playbook-level failures, display formatting | Ansible task failures, missing variables |
| **Business Logic** | Operation errors, parameter validation, batch error collection | Invalid network ranges, API operation failures |
| **Infrastructure** | HTTP errors, authentication, session management | Connection timeouts, 403 authentication errors |
| **External Systems** | API responses, device availability | DefensePro device errors, malformed responses |

## Module Architecture

### Core Components (Infrastructure Layer)

1. **RadwareCC** (`plugins/module_utils/radware_cc.py`)
   - **Purpose**: HTTP client with intelligent session management
   - **Features**: 
     - Automatic re-authentication on 403 errors
     - Session persistence with configurable lifetime
     - Request/response logging and error handling
     - SSL verification control (disabled by default for internal networks)
   - **Session Storage**: `./tmp/radware_cc_sessions/` or system temp directory

2. **Logger** (`plugins/module_utils/logger.py`)
   - **Purpose**: Structured logging with verbosity levels
   - **Features**:
     - File-based logging with rotation (`playbooks/log/log_YYYYMMDD.log`)
     - Configurable levels: `disabled`, `info`, `debug`
     - Timestamp and module identification
     - Safe credential handling (no passwords in logs)

### Business Logic Modules (Business Logic Layer)

3. **Network Class Modules** (`plugins/modules/`)
   - **Enhancement**: All modules follow consistent unified pattern
   - **Key Features**:
     - Single device call with batch processing (moved from YAML loops to Python)
     - Enhanced error handling using `cc._request` methods
     - Structured `debug_info` and comprehensive logging
     - Check mode with preview functionality showing exact operations
     - Formatted output with success/failure indicators
     - List-based filtering support for get operations
   - **Modules**: `create_network_class.py`, `edit_network_class.py`, `delete_network_class.py`, `get_network_class.py`

4. **Connection Limit Profile Modules** (`plugins/modules/`) - **Architecture v0.1.4+**
   - **Purpose**: Creation and editing of connection limit protection subprofiles
   - **Features**: Profile creation, protection attachment, filtering, deletion
   - **Architecture Highlights**:
     - Creation: `create_cl_configuration.py` (loops/mapping in Python)
     - Editing: `edit_cl_configuration.py` (per-device call, internal protection loop)
     - Getting: `get_cl_configuration.py` (fetches profiles+protections, maps values, supports filtering)
     - Deleting: `delete_cl_configuration.py` (flexible removal with dependency handling)
   - **Key Improvements**: 
     - Both `cl_protections` and `cl_profiles` sections are optional for creation
     - For editing: only specify parameters to change (partial update)
     - Centralized mapping and error handling in Python vs. complex YAML loops

5. **Security Policy Modules** (`plugins/modules/`)
   - **Purpose**: Unified orchestration for security policy creation, editing, and deletion with profile management
   - **Features**: Policy creation, policy editing, policy deletion, profile binding, orchestration control
   - **Architecture Highlights**:
     - Creation: `create_security_policy.py` (API call with profile bindings)
     - Editing: `edit_security_policy.py` (partial updates with profile attachment/detachment)
     - Deletion: `delete_security_policy.py` (dual deletion modes with optional profile cleanup)
     - Orchestration: `create_security_policy.yml` (coordinates profiles creation, and policies)
     - Editing: `edit_security_policy.yml` (modifies existing policies with conditional locking)
     - Deletion: `delete_security_policy.yml` (removes policies with flexible cleanup options)
   - **Key Features**:
     - Unified orchestration with control flags for each creation stage
     - Partial updates for editing (only specify parameters to change)
     - Profile attachment and detachment (empty string to detach)
     - Dual deletion modes (policy-only vs policy+profiles cleanup)
     - Preview mode for all operations to validate changes before execution
     - Different protection profile types bindable to policies
     - User-friendly parameter mapping (e.g., "block_and_report" → "1", "inbound" → "1")
     - Comprehensive error handling with detailed failure reporting
     - Preview mode support for orchestration planning

6. **BDoS Modules** (`plugins/modules/`)
   - **Enhancement**: All modules follow consistent unified pattern
   - **Key Features**:
     - Single device call with batch processing (moved from YAML loops to Python)
     - Enhanced error handling using `cc._request` methods
     - Structured `debug_info` and comprehensive logging
     - Check mode with preview functionality showing exact operations
     - Formatted output with success/failure indicators
     - List-based filtering support for get operations
   - **Modules**: `create_bdos_profile.py`, `edit_bdos_profile.py`, `delete_bdos_profile.py`, `get_bdos_profile.py`

   6. **DNS Modules** (`plugins/modules/`)
   - **Enhancement**: All modules follow consistent unified pattern
   - **Key Features**:
     - Single device call with batch processing (moved from YAML loops to Python)
     - Enhanced error handling using `cc._request` methods
     - Structured `debug_info` and comprehensive logging
     - Check mode with preview functionality showing exact operations
     - Formatted output with success/failure indicators
     - List-based filtering support for get operations
   - **Modules**: `create_dns_profile.py`, `edit_dns_profile.py`, `delete_dns_profile.py`, `get_dns_profile.py`

## API Endpoints

### Network Class Management
| Operation | Method | Endpoint |
|-----------|--------|----------|
| **Create** | POST | `/mgmt/device/byip/{dp_ip}/config/rsBWMNetworkTable/{class_name}/{index}` |
| **Edit** | PUT | `/mgmt/device/byip/{dp_ip}/config/rsBWMNetworkTable/{class_name}/{index}` |
| **Delete** | DELETE | `/mgmt/device/byip/{dp_ip}/config/rsBWMNetworkTable/{class_name}/{index}` |
| **Get** | GET | `/mgmt/device/byip/{dp_ip}/config/rsBWMNetworkTable/{class_name}/{index}` |

### Device Locking
| Operation | Method | Endpoint |
|-----------|--------|----------|
| **Lock** | POST | `/mgmt/device/byip/{dp_ip}/config/lock` |
| **Unlock** | POST | `/mgmt/device/byip/{dp_ip}/config/unlock` |

### Connection Limit Profile Management
| Operation | Method | Endpoint |
|-----------|--------|----------|
| **Create Protection** | POST | `/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable/{index}` |
| **Edit Protection** | PUT | `/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable/{index}` |
| **Create Profile** | POST | `/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitProfileTable/{profile_name}/{protection_name}` |
| **Get Profiles** | GET | `/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitProfileTable` |
| **Get Protections** | GET | `/mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable` |

**Note**: `{index}` parameter:
- Optional in variables (defaults to 0)
- Valid values: 0 or next available starting from 450001+
- Used in URL path for both creation and editing operations

### BDoS Profile Management
| Operation | Method | Endpoint |
|-----------|--------|----------|
| **Create Profile** | POST | `/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}` |
| **Edit Profile** | PUT | `/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}` |
| **Delete Profile** | DELETE | `/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}` |
| **Get Profiles** | GET | `/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}` |

### Security Policy Management

| Operation | HTTP Method | API Endpoint |
|-----------|-------------|--------------|
| Create Security Policy | POST | `/mgmt/device/byip/{ip}/config/rsIDSNewRulesTable/{policy_name}` |
| Edit Security Policy | PUT | `/mgmt/device/byip/{ip}/config/rsIDSNewRulesTable/{policy_name}` |

**Parameters**: Minimal required parameters with optional advanced configuration
**Profile Bindings**: Different protection profile types supported
**Response**: Policy creation/modification status with error details

**Key Features**:
- **Minimal Parameters**: Only `policy_name` is mandatory for creation/editing - DefensePro provides defaults
- **Conditional Parameter Sending**: Only user-specified parameters sent to API
- **Partial Updates**: For editing, only specify parameters to change - unspecified parameters remain unchanged
- **Profile Management**: Attach profiles by name, detach with empty string ("")
- **User-Friendly Value Mapping**: Automatic conversion of human-readable values to API codes
- **Flexible Configuration**: Full parameter support when needed

### DNS Profile Management
| Operation | Method | Endpoint |
|-----------|--------|----------|
| **Create** | POST | `/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}` |
| **Edit** | PUT | `/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}` |
| **Delete** | DELETE | `/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}` |
| **Get** | GET | `/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}` |

### Policy Update Management

| Operation | HTTP Method | API Endpoint |
|-----------|-------------|--------------|
| Apply Policy Updates | POST | `/mgmt/device/byip/{dp_ip}/config/updatepolicies` |

**Purpose**: Apply pending DefensePro configuration changes (commit configurations)

**Module**: `plugins/modules/update_policies.py`

**Payload**: None (DefensePro IP specified in URL path)

**Configuration**: `vars/update_vars.yml` and `vars/update_vars_example.yml`

**API Pattern**:
```
POST /mgmt/device/byip/10.105.192.32/config/updatepolicies
# No request body needed
```

**Key Features**:
- Must be called while device is locked
- Commits ALL pending configuration changes
- Supports both standalone and orchestrated execution modes

**Conditional Execution Modes**:
- **Automatic**: Integrated into orchestration playbooks with `apply_policies_after_creation: true`
- **Manual**: Standalone `update_policies.yml` playbook for selective updates
- **Conditional**: Controlled by `skip_policy_updates` variable in orchestrated flows
- **Safety**: Optional interactive confirmation prompts in standalone mode

**Device Lock/Unlock Integration**:
- **Centralized Locking**: Orchestration playbook "create_security_policy.yml" handle device locking centrally
- **Always Unlock**: Devices are unlocked even if operations fail


**Usage Pattern**:
```python
# In orchestration workflow - centralized locking with conditional skipping
- name: "Centralized Device Locking for Orchestration"
  dp_lock:
    provider: "{{ cc }}"
    dp_ip: "{{ item }}"
  loop: "{{ dp_ip }}"

# Import sub-playbooks with conditional variables
- import_playbook: create_network_class.yml
  vars:
    skip_policy_updates: true  # Orchestrator handles policy updates
    skip_device_lock: true     # Orchestrator handles locking centrally

# Individual playbook conditional logic  
- name: "Lock device(s)"
  dp_lock:
    provider: "{{ cc }}"
    dp_ip: "{{ item }}"
  when: not (skip_device_lock | default(false))

- name: "Apply policy updates per device"
  update_policies:
    provider: "{{ cc }}"
    dp_ip: "{{ item }}"
  when: 
    - not (skip_policy_updates | default(false))
    - apply_policies_after_creation | default(true)
```

## Module Development Pattern

### Unified Module Structure (v0.1.2.1+)
```python
from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        # Operation-specific parameters
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Setup logging and RadwareCC
    log_level = provider.get('log_level', 'disabled')
    logger = Logger(verbosity=log_level)
    cc = RadwareCC(provider['cc_ip'], provider['username'], 
                  provider['password'], log_level=log_level, logger=logger)
    
    # Structured debug info
    debug_info['input'] = {
        'dp_ip': dp_ip,
        'operation_count': len(items_to_process)
    }
    
    try:
        # Batch processing logic
        changes_made = False
        errors = []
        
        if module.check_mode:
            # Preview mode logic
            pass
        else:
            # Actual operations using cc._request methods
            pass
            
        # Structured response
        result.update({
            'changed': changes_made,
            'response': structured_response,
            'debug_info': debug_info
        })
        
    except Exception as e:
        module.fail_json(msg=str(e), debug_info=debug_info, **result)
```

### Legacy Module Structure
```python
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        # For multi-edit: edit_cl_configuration (list of dicts)
    )
    # ...existing code...
    # For multi-edit modules, loop over protections inside Python, not YAML
    # All mappings (protocol, action, tracking_type, etc.) handled in Python
    # Partial update: only send parameters to change
    # Error handling and logging centralized
    # ...existing code...
```

## Request/Response Patterns

### Create Network Class
```json
POST /mgmt/device/byip/10.105.192.32/config/rsBWMNetworkTable/web_servers/0

{
    "rsBWMNetworkName": "web_servers",
    "rsBWMNetworkSubIndex": 0,
    "rsBWMNetworkAddress": "192.168.1.0", 
    "rsBWMNetworkMask": "255.255.255.0",
    "rsBWMNetworkMode": "1"
}
```

### Edit Network Class
```json
PUT /mgmt/device/byip/10.105.192.32/config/rsBWMNetworkTable/web_servers/0

{
    "rsBWMNetworkName": "web_servers",
    "rsBWMNetworkAddress": "10.1.1.0",
    "rsBWMNetworkMask": "24"
}
```
### Get Network Classes Response
```json
{
  "rsBWMNetworkTable": [
        {
            "rsBWMNetworkName": "web_servers",
            "rsBWMNetworkSubIndex": "0",
            "rsBWMNetworkAddress": "192.168.1.0",
            "rsBWMNetworkMask": "24",
            "rsBWMNetworkMode": "1",
            "rsBWMNetworkFromIP": "192.168.1.0",
            "rsBWMNetworkToIP": "192.168.1.255"
        }
    ]
}
```

**Features**:
- **List filtering**: `filter_class_names: ["class1", "class2"]`
- **Structured breakdown**: Groups entries by class name
- **Enhanced summary**: Statistics and filter information
- **Formatted output**: Human-readable display in playbooks

## Error Handling

### Unified Error Handling Pattern (v0.1.2.1+)
All modules now use consistent `cc._request` methods for HTTP operations:

```python
try:
    # Use cc._request methods for consistent error handling
    resp = cc._post(url, json=body)
    if resp.status_code == 200:
        # Success logic
        pass
    else:
        # Error handled by cc._request
        errors.append(f"Failed operation: {resp.text}")
except Exception as e:
    errors.append(f"Request failed: {str(e)}")
```

### Create Security Policy
```python
# Request
url = f"/mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable/{policy_name}"
body = {
    "rsIDSNewRulesDirection": "1",           # Mapped from "inbound"
    "rsIDSNewRulesAction": "1",              # Mapped from "block_and_report"
    "rsIDSNewRulesPriority": "100", 
    "rsIDSNewRulesProfileConlmt": "web_cl_profile",  # Profile binding
    # ... additional profile bindings
}
resp = cc._post(url, json=body)

# Response (Success)
{
    "status": "success",
    "message": "Policy created successfully"
}

# Response (Error) 
{
    "status": "error", 
    "message": "M_00386: An entry with same key already exists."
}
```

### HTTP Error Patterns
```python
try:
    resp = cc._post(url, json=body)
    data = resp.json()
except requests.exceptions.HTTPError as err:
    if err.response.status_code == 403:
        # Re-authentication handled automatically by RadwareCC
        pass
    elif err.response.status_code == 404:
        # Resource not found
        pass
except ValueError:
    # Invalid JSON response
    raise Exception(f"Invalid JSON response: {resp.text}")
```

### Module Error Reporting
```python
try:
    # Operation logic
    pass
except Exception as e:
    logger.error(f"Operation failed: {str(e)}")
    module.fail_json(
        msg=str(e), 
        debug_info=debug_info,
        **result
    )
```

### Delete Security Policy

**Module**: `delete_security_policy.py`  
**Playbook**: `delete_security_policy.yml`  
**Variables**: `delete_vars.yml` (delete_security_policies section)

**Purpose**: Remove security policies with optional profile cleanup

**Key Features**:
- **Dual Deletion Modes**: Simple policy deletion or complex policy+profiles deletion
- **Safe Default**: Policy-only deletion preserves profiles for other policies
- **Batch Processing**: Delete multiple policies in a single operation
- **Preview Mode**: Check mode shows planned deletions before execution
- **Conditional Execution**: Device locking/unlocking can be skipped with control flags

**Deletion Modes**:
1. **`policy_only` (default/recommended)**:
   - Endpoint: `DELETE /mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable/{policy_name}`
   - Safe deletion - only removes the policy
   - Associated profiles remain available for other policies
   - Use for most deletion scenarios

2. **`policy_and_profiles` (advanced)**:
   - Endpoint: `DELETE /mgmt/device/byip/{dp_ip}/config/deletenetworktemplatelist`
   - May remove associated profiles if no longer used by other policies
   - Use with caution - may affect other policies
   - Only use when certain about profile cleanup requirements

**Variables Structure** (`delete_vars.yml`):
```yaml
delete_security_policies:
  - policy_name: "test_security_policy"     # MANDATORY: Policy name to delete
    deletion_mode: "policy_only"            # OPTIONAL: policy_only | policy_and_profiles
  
  - policy_name: "old_security_policy"     # MANDATORY: Policy name to delete  
    deletion_mode: "policy_and_profiles"    # OPTIONAL: Advanced cleanup mode
    
  # deletion_mode defaults to "policy_only" if not specified
  - policy_name: "another_policy"           # Uses default safe deletion mode
```

**API Endpoints**:
```python
# Policy-only deletion (safe, default)
url = f"{config.BASE_URL}/config/rsIDSNewRulesTable/{policy_name}"
resp = cc._delete(url)

# Policy and profiles deletion (advanced)
url = f"{config.BASE_URL}/config/deletenetworktemplatelist"
body = {"rsIDSNewRulesTable": [{"Name": policy_name}]}
resp = cc._delete(url, json=body)
```

**Usage Recommendations**:
- Use `policy_only` mode for shared environments where profiles may be used by multiple policies
- Use `policy_and_profiles` mode only when certain that associated profiles should be cleaned up
- Always test in preview mode first with `policy_and_profiles` to understand impact
- Consider manual profile cleanup after policy deletion for better control

## Session Management

### Session Persistence
- Sessions stored in `./tmp/radware_cc_sessions/` (preferred) or system temp
- Session lifetime: 600 seconds (configurable)
- Automatic cleanup of expired sessions
- Hash-based session keys for multi-user environments

### Session File Format
```
session_{md5_hash}.pkl    # Pickled cookies
session_{md5_hash}.time   # Creation timestamp
```

## Logging

### Log Levels
- `disabled`: No logging
- `info`: Operational messages
- `debug`: Detailed request/response data

### Log Location
- File: `playbooks/log/log_YYYYMMDD.log`
- Format: `[TIMESTAMP] [LEVEL] [MODULE] Message`

### Example Log Output
```
[2025-08-28 17:30:45] [INFO] [RadwareCC] Logging in to Radware CC at 10.105.193.3 as radware
[2025-08-28 17:30:45] [INFO] [create_network_class] Creating network class web_servers at index 0
[2025-08-28 17:30:46] [DEBUG] [RadwareCC] Response status: 200
```

## Testing

### Unit Testing
```bash
# Syntax validation
python3 -m py_compile plugins/modules/create_dns_profile.py

# YAML validation  
python3 -c "import yaml; yaml.safe_load(open('vars/create_vars.yml'))"

# Ansible module testing
ansible-doc -t module plugins/modules/create_dns_profile.py
```

### Integration Testing
```bash
# Check mode (dry run)
ansible-playbook --check playbooks/create_dns_profile.yml

# Single device testing
# Edit vars file to target one device, then run normally
ansible-playbook playbooks/create_dns_profile.yml
```

## Extending the Modules

### Adding New Operations

1. **Create/Edit Module** (`plugins/modules/create_cl_configuration.py` or `edit_cl_configuration.py`)
    - Follow the standard module pattern
    - For multi-edit, move all looping/mapping to Python
    - Add proper documentation strings
    - Implement  error handling and logging

2. **Create/Edit Playbook** (`playbooks/create_cl_profiles.yml` or `edit_cl_protections.yml`)
    - Use per-device loop, pass list of items to module
    - Include device locking/unlocking
    - Add descriptive loop labels

3. **Create/Edit Variables** (`vars/edit_vars.yml.example`)
    - Document all parameters
    - Provide usage examples (see USER_GUIDE.md)
    - Add to .gitignore pattern

### Adding New Endpoints

1. **Research API** - Use CyberController API documentation
2. **Add to RadwareCC** - If new HTTP methods needed
3. **Test Manually** - Use curl/postman first
4. **Implement Module** - Following existing patterns

## API Reference

### RadwareCC Class Methods
```python
cc._get(url)                          # GET request
cc._post(url, data=None, json=None)   # POST request  
cc._put(url, data=None, json=None)    # PUT request
cc._delete(url)                       # DELETE request
```

### Logger Class Methods
```python
logger.info(message)     # Info level
logger.debug(message)    # Debug level
logger.error(message)    # Error level
```


## Security Considerations

- **Credential Storage**: Variables in git-ignored files
- **Session Security**: Temporary session storage with cleanup
- **SSL Verification**: Configurable (disabled by default for internal networks)
- **Error Sanitization**: No credentials in error messages or logs

## Contributing

1. **Follow Patterns**: Use existing modules as templates
2. **Test Thoroughly**: Unit tests + integration tests + manual testing
3. **Document**: Update both user and developer documentation
4. **Version Control**: Feature branches with descriptive names

---

**Need user instructions?** See [USER_GUIDE.md](USER_GUIDE.md) for operational procedures and configuration examples.