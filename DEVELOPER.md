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
│   ├── ansible.cfg              # Ansible runtime configuration
│   ├── ansible_example.cfg      # Template for ansible.cfg  
│   ├── inventory.ini            # Ansible hosts (usually just 'cc')
│   └── inventory_example.ini    # Template for inventory.ini
├── 
├── 📁 Documentation  
│   ├── README.md                # Project overview and quick start
│   ├── USER_GUIDE.md            # Step-by-step operational guide
│   └── DEVELOPER.md             # Technical architecture (this file)
├── 
├── 📁 playbooks/                # ORCHESTRATION LAYER
│   ├── 🎯 Network Class Operations
│   │   ├── create_network_class.yml    # Create network classes
│   │   ├── edit_network_class.yml      # Modify network classes  
│   │   ├── delete_network_class.yml    # Remove network classes
│   │   └── get_network_class.yml       # Query network classes
│   ├── 🎯 Connection Limit Operations  
│   │   ├── create_cl_profiles.yml      # Create CL profiles/protections
│   │   ├── edit_cl_protections.yml     # Edit CL protections
│   │   ├── get_cl_profiles.yml         # Query CL profiles
│   │   └── delete_cl_profiles.yml      # Delete CL profiles/protections
│   ├── 🎯 BDoS Flood Profile Operations
│   │   ├── create_bdos_profile.yml     # Create BDoS Flood profiles
│   │   ├── edit_bdos_profile.yml       # Modify BDoS Flood profiles
│   │   ├── delete_bdos_profile.yml     # Remove BDoS Flood profiles
│   │   └── get_bdos_profile.yml       # Query BDoS Flood profiles
│   ├── 🎯 Security Policy Operations
│   │   ├── create_security_policy.yml  # Create security policies with orchestration
│   │   ├── edit_security_policy.yml    # Edit existing security policies
│   │   └── delete_security_policy.yml  # Delete security policies with cleanup options
│   ├── 📊 Runtime Data (auto-created)
│   │   ├── log/                        # Execution logs by date
│   │   │   └── log_YYYYMMDD.log        # Daily log files
│   │   └── tmp/                        # Temporary files  
│   │       └── radware_cc_sessions/    # Session cache files
├── 
├── 📁 plugins/                 # BUSINESS LOGIC & UTILITIES
│   ├── 📁 modules/             # BUSINESS LOGIC LAYER
│   │   ├── 🔧 Network Class Modules (Unified Architecture v0.1.2.2+)
│   │   │   ├── create_network_class.py  # Batch creation with error collection
│   │   │   ├── edit_network_class.py    # Batch editing with preview mode
│   │   │   ├── delete_network_class.py  # Batch deletion with validation  
│   │   │   └── get_network_class.py     # Enhanced querying with filtering
│   │   ├── 🔧 Connection Limit Modules (v0.1.4+)
│   │   │   ├── create_cl_configuration.py  # Create protections & profiles
│   │   │   ├── edit_cl_configuration.py    # Edit protections (partial updates)
│   │   │   ├── get_cl_configuration.py     # Get profiles with filtering
│   │   │   └── delete_cl_configuration.py  # Delete with dependency handling
│   │   ├── 🔧 BDoS Flood Profile Modules (v0.1.3+)
│   │   │   ├── create_bdos_profile.py      # Batch creation with validation
│   │   │   ├── edit_bdos_profile.py        # Modify existing BDoS profiles
│   │   │   ├── delete_bdos_profile.py      # Batch deletion with error handling
│   │   │   └── get_bdos_profile.py        # Query BDoS Flood profiles
│   │   ├── 🔧 Security Policy Modules (v0.2.0+)
│   │   │   ├── create_security_policy.py   # Create policies with profile bindings
│   │   │   ├── edit_security_policy.py     # Edit policies (partial updates)
│   │   │   └── delete_security_policy.py   # Delete policies (dual deletion modes)
│   │   └── 🔧 Device Management
│   │       ├── dp_lock.py                  # Device configuration lock
│   │       └── dp_unlock.py                # Device configuration unlock
│   └── 📁 module_utils/        # INFRASTRUCTURE LAYER
│       ├── radware_cc.py                # HTTP client with session management
│       └── logger.py                    # Structured logging with rotation
├── 
├── 📁 vars/                    # CONFIGURATION & DATA LAYER
│   ├── 🔗 Connection Configuration
│   │   ├── cc.yml                     # CyberController connection (git-ignored)
│   │   └── cc_example.yml             # Template for cc.yml
│   ├── 🎯 Operation Variables (git-ignored)
│   │   ├── create_vars.yml            # Variables for creation operations
│   │   ├── edit_vars.yml              # Variables for editing operations  
│   │   ├── delete_vars.yml            # Variables for deletion operations
│   │   ├── get_vars.yml               # Variables for query operations
│   │   └── update_vars.yml            # Variables for policy update operations
│   └── 📋 Variable Templates (in git)
│       ├── create_vars.yml.example    # Template for create_vars.yml
│       ├── edit_vars.yml.example      # Template for edit_vars.yml
│       ├── delete_vars.yml.example    # Template for delete_vars.yml
│       ├── get_vars.yml.example       # Template for get_vars.yml
│       └── update_vars_example.yml    # Template for update_vars.yml 
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


## API Endpoints

### Network Class Management
| Operation | Method | Endpoint |
|-----------|--------|----------|
| **Create** | POST | `/mgmt/device/byip/{dp_ip}/config/rsBWMNetworkTable/{class_name}/{index}` |
| **Edit** | PUT | `/mgmt/device/byip/{dp_ip}/config/rsBWMNetworkTable/{class_name}/{index}` |
| **Delete** | DELETE | `/mgmt/device/byip/{dp_ip}/config/rsBWMNetworkTable/{class_name}/{index}` |
| **Get** | GET | `/mgmt/v2/devices/{dp_ip}/config/itemlist/rsBWMNetworkTable[/{class_name}` |

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
| **Create Profile** | POST | `/mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable/{profile_name}` |
| **Edit Profile** | PUT | `/mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable/{profile_name}` |
| **Create Profile** | POST | `/mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable/{profile_name}` |
| **Get Profiles** | GET | `/mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable/{profile_name}` |


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

### Create Connection Limit Protection
```json
POST /mgmt/device/byip/10.105.192.32/config/rsIDSConnectionLimitAttackTable/{index}

{
    "rsIDSConnectionLimitAttackName": "cl_prot_tcp_limit",
    "rsIDSConnectionLimitAttackProtocol": "2",
    "rsIDSConnectionLimitAttackThreshold": "100",
    "rsIDSConnectionLimitAttackTrackingType": "2",
    "rsIDSConnectionLimitAttackReportMode": "10",
    "rsIDSConnectionLimitAttackPacketReport": "2",
    "rsIDSConnectionLimitAttackType": "1"
}
```
### Edit Connection Limit Protections
```json
PUT /mgmt/device/byip/10.105.192.32/config/rsIDSConnectionLimitAttackTable/{index}

{
    "rsIDSConnectionLimitAttackName": "cl_prot_tcp_limit",
    "rsIDSConnectionLimitAttackProtocol": "2",
    "rsIDSConnectionLimitAttackThreshold": "100",
    "rsIDSConnectionLimitAttackTrackingType": "2",
    "rsIDSConnectionLimitAttackReportMode": "10",
    "rsIDSConnectionLimitAttackPacketReport": "2",
    "rsIDSConnectionLimitAttackType": "1"
}
```

**Usage:**
- Call `edit_cl_configuration` once per device, pass list of protections to edit
- Each protection dict must include `protection_index` (mandatory), and any parameters to change
- All mappings handled internally

**Index Parameter**:
- **Optional**: Defaults to 0 if not specified in variables
- **Valid Values**: 0 (default) or next available starting from 450001+
- **API Behavior**: Index becomes part of the URL path for creation and editing
```

### Create Connection Limit Profile
```json
POST /mgmt/device/byip/10.105.192.32/config/rsIDSConnectionLimitProfileTable/web_limits/cl_prot_tcp_limit

{
    "rsIDSConnectionLimitProfileName": "web_limits",
    "rsIDSConnectionLimitProfileAttackName": "cl_prot_tcp_limit"
}
```

### Get Connection Limit Profiles Response (New Architecture)
```json
GET /mgmt/device/byip/10.105.192.32/config/rsIDSConnectionLimitProfileTable
GET /mgmt/device/byip/10.105.192.32/config/rsIDSConnectionLimitAttackTable

Response (mapped and combined):
{
    "profiles": [
        {
            "profile_name": "cl_prof_egor_test10",
            "protections": [
                {
                    "protection_name": "cl_prot_egor_test10",
                    "protection_id": "450141", 
                    "protection_type": "cps",
                    "tracking_type": "dst_ip",
                    "protocol": "tcp",
                    "threshold": "50",
                    "action": "drop",
                    "packet_report": "enable",
                    "app_port_group": "http"
                }
            ]
        }
    ]
}
```

**Usage:**
- Call `get_cl_configuration` once per device
- Optional filtering: `filter_cl_profile_names: ["profile1", "profile2"]`
- All API mappings handled internally (reverse of create/edit logic)
- Returns nested structure: profiles -> protections -> subsettings

### Delete Connection Limit Profiles and Protections (`delete_cl_configuration`)

**Purpose**: Delete connection limit protections and profiles with flexible options.

**Module**: `plugins/modules/delete_cl_configuration.py`

**API Endpoints**:
- Remove protection from profile: `DELETE /mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitProfileTable/{profile_name}/{protection_name}`
- Delete protection entirely: `DELETE /mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable/{protection_id}`

**Input Parameters**:
```yaml
# OPTIONAL: Remove protections from profiles (profile auto-deleted when last protection removed)
cl_profile_deletions:
  - profile_name: "cl_prof_egor_test10"
    protections:
      - "cl_prot_egor_test10"
      - "cl_prot_egor_test11"
      - "cl_prot_egor_test12"
  
  - profile_name: "another_profile"
    protections:
      - "protection_to_remove"

# OPTIONAL: Delete protections entirely (protection must not be in any profile)
# The format supporting both names and indexes:
cl_protection_deletions:
  - protections_to_delete:
      - "protection_name_1"      # Delete by name (module looks up index)
      - "protection_name_2"      # Delete by name (module looks up index)
      - 450001                   # Delete by index directly
      - 450002                   # Delete by index directly
```

**Key Features**:
- Protection cannot be deleted if still associated with any profile
- Profile is automatically deleted when last protection is removed
- Both sections are optional - define based on your needs
- Order: profile deletions processed first, then protection deletions
- **Format**: Single list supporting both names (strings) and indexes (integers)
- **Smart processing**: Module fetches current protections only when string names are used
- **Enhanced validation**: Check mode validates both names and indexes against device state

**API Endpoints**:
- Get current protections (conditional): `GET /mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable`
- Remove protection from profile: `DELETE /mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitProfileTable/{profile_name}/{protection_name}`
- Delete protection entirely: `DELETE /mgmt/device/byip/{dp_ip}/config/rsIDSConnectionLimitAttackTable/{protection_id}`

**Usage:**
- Call `delete_cl_configuration` once per device
- Both `cl_profile_deletions` and `cl_protection_deletions` are optional
- Module handles error reporting for failed operations
- **No need to know indexes**: Just specify protection names, module handles name-to-index mapping
- Configure deletions in `delete_vars.yml` (consolidated with network class deletions)

### Get Network Classes Response
```json
{
    "rsBWMNetworkTable": [...],  // Raw API response
    "classes_breakdown": {
        "web_servers": [
            {
                "rsBWMNetworkName": "web_servers",
                "rsBWMNetworkSubIndex": "0",
                "rsBWMNetworkAddress": "192.168.1.0",
                "rsBWMNetworkMask": "24",
                "rsBWMNetworkFromIP": "192.168.1.0",
                "rsBWMNetworkToIP": "192.168.1.255"
            }
        ]
    },
    "summary": {
        "class_names": ["web_servers", "db_servers"],
        "total_entries": 5,
        "unique_classes": 2,
        "filtered": true,
        "filter_applied": ["web_servers"]
    }
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
###  Create BDoS Profile 
```json
POST /mgmt/device/byip/10.105.192.32/config/rsIDSNewRulesTable/{profile_name}

{
    "rsIDSNewRulesName": "BDOS_Profile_5",
    "rsIDSNewRulesAction": "2",
    "rsIDSNewRulesSynFlood": "1",
    "rsIDSNewRulesUdpFlood": "1",
    "rsIDSNewRulesIgmpFlood": "0",
    "rsIDSNewRulesIcmpFlood": "1",
    "rsIDSNewRulesTcpAckFinFlood": "0",
    "rsIDSNewRulesTcpRstFlood": "0",
    "rsIDSNewRulesTcpPshAckFlood": "0",
    "rsIDSNewRulesTcpSynAckFlood": "0",
    "rsIDSNewRulesTcpFragFlood": "0",
    "rsIDSNewRulesUdpFragFlood": "0",
    "rsIDSNewRulesInboundTraffic": 1000000,
    "rsIDSNewRulesOutboundTraffic": 500000,
    "rsIDSNewRulesTcpInQuota": 50,
    "rsIDSNewRulesUdpInQuota": 50,
    "rsIDSNewRulesIcmpInQuota": 50,
    "rsIDSNewRulesIgmpInQuota": 50,
    "rsIDSNewRulesTcpOutQuota": 50,
    "rsIDSNewRulesUdpOutQuota": 50,
    "rsIDSNewRulesIcmpOutQuota": 50,
    "rsIDSNewRulesIgmpOutQuota": 50,
    "rsIDSNewRulesTransparentOptimization": "1",
    "rsIDSNewRulesPacketReport": "1",
    "rsIDSNewRulesBurstAttack": "0",
    "rsIDSNewRulesMaxIntervalBetweenBursts": 60,
    "rsIDSNewRulesLearningSuppressionThreshold": 10,
    "rsIDSNewRulesFootprintStrictness": 2,
    "rsIDSNewRulesRateLimit": 3,
    "rsIDSNewRulesUserDefinedRateLimit": 500,
    "rsIDSNewRulesUserDefinedRateLimitUnit": 2,
    "rsIDSNewRulesAdvancedUdpDetection": "1"
}
```
### Edit BDoS Profile
```json

PUT /mgmt/device/byip/10.105.192.32/config/rsIDSNewRulesTable/{profile_name}

{
    "rsIDSNewRulesName": "BDOS_Profile_5",
    "rsIDSNewRulesAction": "1",
    "rsIDSNewRulesSynFlood": "0",
    "rsIDSNewRulesUdpFlood": "0",
    "rsIDSNewRulesIcmpFlood": "0",
    "rsIDSNewRulesInboundTraffic": 2000000,
    "rsIDSNewRulesOutboundTraffic": 1000000
}
```

Usage:
Call edit_bdos_configuration once per device, passing list of profiles to edit.
Each profile dict must include profile_name (mandatory) and any parameters to change


### Get BDoS Profile 
```json
GET /mgmt/device/byip/10.105.192.32/config/rsIDSNewRulesTable

Response:
{
    "rsNetFloodProfileTable": [
        {
            "rsNetFloodProfileName": "BDoS_Test1",
            "rsNetFloodProfileTcpStatus": "2",
            "rsNetFloodProfileTcpSynStatus": "2",
            "rsNetFloodProfileUdpStatus": "2",
            "rsNetFloodProfileIgmpStatus": "2",
            "rsNetFloodProfileIcmpStatus": "2",
            "rsNetFloodProfileTcpFinAckStatus": "2",
            "rsNetFloodProfileTcpRstStatus": "2",
            "rsNetFloodProfileTcpPshAckStatus": "2",
            "rsNetFloodProfileTcpSynAckStatus": "2",
            "rsNetFloodProfileTcpFragStatus": "2",
            "rsNetFloodProfileBandwidthIn": "40000",
            "rsNetFloodProfileBandwidthOut": "40000",
            "rsNetFloodProfileTcpInQuota": "75",
            "rsNetFloodProfileUdpInQuota": "50",
            "rsNetFloodProfileIcmpInQuota": "3",
            "rsNetFloodProfileIgmpInQuota": "3",
            "rsNetFloodProfileTcpOutQuota": "75",
            "rsNetFloodProfileUdpOutQuota": "50",
            "rsNetFloodProfileIcmpOutQuota": "3",
            "rsNetFloodProfileIgmpOutQuota": "3",
            "rsNetFloodProfileTransparentOptimization": "2",
            "rsNetFloodProfileAction": "1",
            "rsNetFloodProfileLevelOfReuglarzation": "2",
            "rsNetFloodProfileBurstEnabled": "1",
            "rsNetFloodProfileNoBurstTimeout": "30",
            "rsNetFloodProfileBurstAttackThreshold": "5",
            "rsNetFloodProfileBurstAttackPeriod": "12",
            "rsNetFloodProfileOverMitigationStatus": "2",
            "rsNetFloodProfileOverMitigationThreshold": "25",
            "rsNetFloodProfileLearningSuppressionThreshold": "0",
            "rsNetFloodProfileFootprintStrictness": "0",
            "rsNetFloodProfileRateLimit": "0",
            "rsNetFloodProfileUserDefinedRateLimit": "0",
            "rsNetFloodProfileUserDefinedRateLimitUnit": "0",
            "rsNetFloodProfileAdvUdpDetection": "2",
            "rsNetFloodProfileUdpExcludedPorts": "None",
            "rsNetFloodProfileAdvUdpLearningPeriod": "2",
            "rsNetFloodProfileAdvUdpAttackHighEdgeOverride": "0.0",
            "rsNetFloodProfileAdvUdpAttackLowEdgeOverride": "0.0",
            "rsNetFloodProfilePacketReportStatus": "1",
            "rsNetFloodProfilePacketTraceStatus": "2",
            "rsNetFloodProfileUdpFragStatus": "2",
            "rsNetFloodProfileUdpFragInQuota": "25",
            "rsNetFloodProfileUdpFragOutQuota": "25"
        }
    ]
}

#Usage:-
#Call get_bdos_profile once per device
#Optional filtering: filter_bdos_profile_names: ["BDOS_Profile_5"]
#Returns nested structure: profiles -> settings
#API mappings handled internally
```
### Delete BDoS Profile 

DELETE /mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable/{profile_name}

```yml
# Profiles to delete
bdos_profiles:
  - "BDOS_Profile_5"
  - "BDOS_Profile_6"
```
Key Features:
- Profiles cannot be deleted if still associated with any dependent settings
- Module validates existence before deletion
- Order of deletion handled automatically
- Both names and indexes supported internally (no need to provide    index)

### Edit Security Policy
```python
# Request - Partial update (only specified parameters are changed)
url = f"/mgmt/device/byip/{dp_ip}/config/rsIDSNewRulesTable/{policy_name}"
body = {
    "rsIDSNewRulesAction": "0",              # Change action to "report_only"
    "rsIDSNewRulesPriority": "200",          # Change priority
    "rsIDSNewRulesProfileConlmt": "",        # Detach connection limit profile (empty string)
    "rsIDSNewRulesProfileNetflood": "bdos_profile"  # Attach BDOS profile
}
resp = cc._put(url, json=body)

# Response (Success)
{
    "status": "ok"
}

# Response (Error)
{
    "status": "error",
    "message": "M_00001: Policy not found"
}
```

## Security Policy Operations 

### Edit Security Policy

**Module**: `edit_security_policy.py`  
**Playbook**: `edit_security_policy.yml`  
**Variables**: `edit_vars.yml` (edit_security_policies section)

**Purpose**: Modify existing security policies with partial updates and profile management

**Key Features**:
- **Partial Updates**: Only specify parameters to change - unspecified parameters remain unchanged  
- **Profile Management**: Attach profiles by name, detach with empty string ("")
- **Batch Processing**: Edit multiple policies in a single operation
- **Preview Mode**: Check mode shows planned changes before execution
- **Conditional Execution**: Device locking/unlocking can be skipped with control flags

**Variables Structure** (`edit_vars.yml`):
```yaml
edit_security_policies:
  - policy_name: "web_server_protection"    # MANDATORY: Policy name to edit
    # Basic configuration parameters (all optional)
    src_network: "internal_networks"        # Source network class name or "any"
    dst_network: "web_servers"              # Destination network class name or "any"
    direction: "twoway"                     # oneway, twoway, bidirectional
    state: "enable"                         # enable, disable, active, inactive
    action: "block_and_report"              # block_and_report, report_only
    priority: "750"                         # Priority value (1-1000)
    packet_reporting_status: "enable"       # enable, disable
    
    # Profile bindings (all optional - use empty string to remove binding)
    connection_limit_profile: "web_limits"  # Connection limit profile name
    bdos_profile: ""                        # BDOS profile name (empty = detach)
    syn_protection_profile: "syn_limits"    # SYN protection profile name
    # ... additional profile types supported
```

**Usage Pattern**:
```yaml
# Playbook execution 
- name: Edit security policies
  edit_security_policy:
    provider: "{{ radware_cc_provider }}"
    dp_ip: "{{ item }}"
    edit_security_policies: "{{ edit_security_policies }}"
  loop: "{{ dp_ip }}"
```

**API Mapping**:
- `policy_name` → URL path parameter 
- `action: "block_and_report"` → `"rsIDSNewRulesAction": "1"`
- `action: "report_only"` → `"rsIDSNewRulesAction": "0"`
- `connection_limit_profile: ""` → `"rsIDSNewRulesProfileConlmt": ""` (detachment)
- `direction: "twoway"` → `"rsIDSNewRulesDirection": "2"`

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
python3 -m py_compile plugins/modules/create_network_class.py

# YAML validation  
python3 -c "import yaml; yaml.safe_load(open('vars/create_vars.yml'))"

# Ansible module testing
ansible-doc -t module plugins/modules/create_network_class
```

### Integration Testing
```bash
# Check mode (dry run)
ansible-playbook --check playbooks/create_network_class.yml

# Single device testing
# Edit vars file to target one device, then run normally
ansible-playbook playbooks/create_network_class.yml
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