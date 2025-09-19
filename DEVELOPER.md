# DefensePro Configuration Builder - Developer Guide

**Technical documentation for developers working on the DefensePro Ansible modules**

## Prerequisites for Development

Before working with the DefensePro Configuration Builder modules:

### Environment Setup
```bash
# 1. Copy configuration templates
cp ansible_example.cfg ansible.cfg
cp inventory_example.ini inventory.ini

# 2. Set up connection configuration
cd vars/
cp cc_example.yml cc.yml
# Edit cc.yml with your CyberController details

# 3. Install dependencies and verify setup
pip3 install ansible requests
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

## Directory Structure

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
│   │   ├── create_network_class.yml    
│   │   ├── edit_network_class.yml      
│   │   ├── delete_network_class.yml    
│   │   └── get_network_class.yml       
│   ├── 🎯 Connection Limit Operations  
│   │   ├── create_cl_profiles.yml      
│   │   ├── edit_cl_protections.yml     
│   │   ├── get_cl_profiles.yml         
│   │   └── delete_cl_profiles.yml      
│   ├── 🎯 BDoS Flood Profile Operations
│   │   ├── create_bdos_profile.yml     
│   │   ├── edit_bdos_profile.yml       
│   │   ├── delete_bdos_profile.yml     
│   │   └── get_bdos_profile.yml        
│   ├── 🎯 DNS Protection Profile Operations
│   │   ├── create_dns_profile.yml      # Create DNS Protection profiles
│   │   ├── edit_dns_profile.yml        # Modify existing DNS profiles
│   │   ├── delete_dns_profile.yml      # Remove DNS Protection profiles
│   │   └── get_dns_profile.yml         # Query DNS Protection profiles
│   ├── 🎯 Security Policy Operations
│   │   ├── create_security_policy.yml  
│   │   ├── edit_security_policy.yml    
│   │   └── delete_security_policy.yml  
│   ├── 📊 Runtime Data (auto-created)
│   │   ├── log/                        
│   │   │   └── log_YYYYMMDD.log        
│   │   └── tmp/                        
│   │       └── radware_cc_sessions/    
├── 
├── 📁 plugins/                 # BUSINESS LOGIC & UTILITIES
│   ├── 📁 modules/             # BUSINESS LOGIC LAYER
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
│   │   ├── 🔧 BDoS Flood Profile Modules
│   │   │   ├── create_bdos_profile.py      
│   │   │   ├── edit_bdos_profile.py        
│   │   │   ├── delete_bdos_profile.py      
│   │   │   └── get_bdos_profile.py         
│   │   ├── 🔧 DNS Protection Profile Modules
│   │   │   ├── create_dns_profile.py       # Batch creation with validation
│   │   │   ├── edit_dns_profile.py         # Modify DNS profiles
│   │   │   ├── delete_dns_profile.py       # Batch deletion with error handling
│   │   │   └── get_dns_profile.py          # Query DNS profiles
│   │   ├── 🔧 Security Policy Modules
│   │   │   ├── create_security_policy.py   
│   │   │   ├── edit_security_policy.py     
│   │   │   └── delete_security_policy.py   
│   │   └── 🔧 Device Management
│   │       ├── dp_lock.py                  
│   │       └── dp_unlock.py                
│   └── 📁 module_utils/        # INFRASTRUCTURE LAYER
│       ├── radware_cc.py                
│       └── logger.py                    
├── 
├── 📁 vars/                    # CONFIGURATION & DATA LAYER
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

5. **BDoS Modules** (`plugins/modules/`)
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

7. **Security Policy Modules** (`plugins/modules/`)
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
| **Create Profile** | POST | `/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}` |
| **Edit Profile** | PUT | `/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}` |
| **Create Profile** | POST | `/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}` |
| **Get Profiles** | GET | `/mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}` |


### DNS Profile Management
| Operation | Method | Endpoint |
|-----------|--------|----------|
| **Create Profile** | POST | `/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}` |
| **Edit Profile** | PUT | `/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}` |
| **Create Profile** | POST | `/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}` |
| **Get Profiles** | GET | `/mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}` |

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

# Request/Response Patterns

### Create Network Class
```json
# CREATE/EDIT
POST/PUT /mgmt/device/byip/10.105.192.32/config/rsBWMNetworkTable/web_servers/0
{
    "rsBWMNetworkName": "web_servers",
    "rsBWMNetworkAddress": "192.168.1.0", 
    "rsBWMNetworkMask": "255.255.255.0"
}

# GET Response (Enhanced)
{
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

### Create Connection Limit Profile
```json
POST /mgmt/device/byip/10.105.192.32/config/rsIDSConnectionLimitProfileTable/web_limits/cl_prot_tcp_limit

{
    "rsIDSConnectionLimitProfileName": "web_limits",
    "rsIDSConnectionLimitProfileAttackName": "cl_prot_tcp_limit"
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


### Get Connection Limit Profiles Response
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



## Profile operations
###  Create BDoS Profile 
```json
POST /mgmt/device/byip/10.105.192.32/config/rsNetFloodProfileTable/{profile_name}
{
            "rsNetFloodProfileName": "BDOS_Profile_50",
            "rsNetFloodProfileTcpStatus": "2",
            "rsNetFloodProfileTcpSynStatus": "1",
            "rsNetFloodProfileUdpStatus": "1",
            "rsNetFloodProfileIgmpStatus": "1",
            "rsNetFloodProfileIcmpStatus": "1",
            "rsNetFloodProfileTcpFinAckStatus": "1",
            "rsNetFloodProfileTcpRstStatus": "1",
            "rsNetFloodProfileTcpPshAckStatus": "2",
            "rsNetFloodProfileTcpSynAckStatus": "1",
            "rsNetFloodProfileTcpFragStatus": "1",
            "rsNetFloodProfileBandwidthIn": "1000000",
            "rsNetFloodProfileBandwidthOut": "500000",
            "rsNetFloodProfileTcpInQuota": "80",
            "rsNetFloodProfileUdpInQuota": "50",
            "rsNetFloodProfileIcmpInQuota": "10",
            "rsNetFloodProfileIgmpInQuota": "50",
            "rsNetFloodProfileTcpOutQuota": "80",
            "rsNetFloodProfileUdpOutQuota": "50",
            "rsNetFloodProfileIcmpOutQuota": "10",
            "rsNetFloodProfileIgmpOutQuota": "50",
            "rsNetFloodProfileTransparentOptimization": "1",
            "rsNetFloodProfileAction": "0",
            "rsNetFloodProfileLevelOfReuglarzation": "2",
            "rsNetFloodProfileBurstEnabled": "1",
            "rsNetFloodProfileNoBurstTimeout": "60",
            "rsNetFloodProfileBurstAttackThreshold": "5",
            "rsNetFloodProfileBurstAttackPeriod": "32",
            "rsNetFloodProfileOverMitigationStatus": "2",
            "rsNetFloodProfileOverMitigationThreshold": "25",
            "rsNetFloodProfileLearningSuppressionThreshold": "10",
            "rsNetFloodProfileFootprintStrictness": "1",
            "rsNetFloodProfileRateLimit": "3",
            "rsNetFloodProfileUserDefinedRateLimit": "500",
            "rsNetFloodProfileUserDefinedRateLimitUnit": "1",
            "rsNetFloodProfileAdvUdpDetection": "1",
            "rsNetFloodProfileUdpExcludedPorts": "None",
            "rsNetFloodProfileAdvUdpLearningPeriod": "2",
            "rsNetFloodProfileAdvUdpAttackHighEdgeOverride": "0.0",
            "rsNetFloodProfileAdvUdpAttackLowEdgeOverride": "0.0",
            "rsNetFloodProfilePacketReportStatus": "1",
            "rsNetFloodProfilePacketTraceStatus": "2",
            "rsNetFloodProfileUdpFragStatus": "1",
            "rsNetFloodProfileUdpFragInQuota": "25",
            "rsNetFloodProfileUdpFragOutQuota": "25"
        }
```
##### Edit BDoS Profile 
```json
PUT /mgmt/device/byip/10.105.192.32/config/rsNetFloodProfileTable/{profile_name}

{
            "rsNetFloodProfileName": "BDOS_Profile_50",
            "rsNetFloodProfileTcpStatus": "2",
            "rsNetFloodProfileTcpSynStatus": "1",
            "rsNetFloodProfileUdpStatus": "1",
            "rsNetFloodProfileIgmpStatus": "1",
            "rsNetFloodProfileIcmpStatus": "1",
            "rsNetFloodProfileTcpFinAckStatus": "1",
            "rsNetFloodProfileTcpRstStatus": "1",
            "rsNetFloodProfileTcpPshAckStatus": "2",
            "rsNetFloodProfileTcpSynAckStatus": "1",
            "rsNetFloodProfileTcpFragStatus": "1",
            "rsNetFloodProfileBandwidthIn": "1000000",
            "rsNetFloodProfileBandwidthOut": "500000",
            "rsNetFloodProfileTcpInQuota": "80",
            "rsNetFloodProfileUdpInQuota": "50",
            "rsNetFloodProfileIcmpInQuota": "10",
            "rsNetFloodProfileIgmpInQuota": "50",
            "rsNetFloodProfileTcpOutQuota": "80",
            "rsNetFloodProfileUdpOutQuota": "50",
            "rsNetFloodProfileIcmpOutQuota": "10",
            "rsNetFloodProfileIgmpOutQuota": "50",
            "rsNetFloodProfileTransparentOptimization": "1",
            "rsNetFloodProfileAction": "0",
            "rsNetFloodProfileLevelOfReuglarzation": "2",
            "rsNetFloodProfileBurstEnabled": "1",
            "rsNetFloodProfileNoBurstTimeout": "60",
            "rsNetFloodProfileBurstAttackThreshold": "5",
            "rsNetFloodProfileBurstAttackPeriod": "32",
            "rsNetFloodProfileOverMitigationStatus": "2",
            "rsNetFloodProfileOverMitigationThreshold": "25",
            "rsNetFloodProfileLearningSuppressionThreshold": "10",
            "rsNetFloodProfileFootprintStrictness": "1",
            "rsNetFloodProfileRateLimit": "3",
            "rsNetFloodProfileUserDefinedRateLimit": "500",
            "rsNetFloodProfileUserDefinedRateLimitUnit": "1",
            "rsNetFloodProfileAdvUdpDetection": "1",
            "rsNetFloodProfileUdpExcludedPorts": "None",
            "rsNetFloodProfileAdvUdpLearningPeriod": "2",
            "rsNetFloodProfileAdvUdpAttackHighEdgeOverride": "0.0",
            "rsNetFloodProfileAdvUdpAttackLowEdgeOverride": "0.0",
            "rsNetFloodProfilePacketReportStatus": "1",
            "rsNetFloodProfilePacketTraceStatus": "2",
            "rsNetFloodProfileUdpFragStatus": "1",
            "rsNetFloodProfileUdpFragInQuota": "25",
            "rsNetFloodProfileUdpFragOutQuota": "25"
        }
```
Usage:
Call edit_bdos_profile once per device, passing list of profiles to edit.
Each profile dict must include profile_name (mandatory) and any parameters to change

####################### Get BDoS Profile ##########################
#### Get BDoS Profile 
```json
GET /mgmt/device/byip/10.105.192.32/config/rsNetFloodProfileTable/{profile_name}

GET /mgmt/device/byip/10.105.192.32/config/rsNetFloodProfileTable/{profile_name}

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
```
#Usage:-
#Call get_bdos_profile once per device
#Optional filtering: filter_bdos_profile_names: ["BDOS_Profile_5"]
#Returns nested structure: profiles -> settings
#API mappings handled internally

### Delete BDoS Profile ###
```yml
DELETE /mgmt/device/byip/{dp_ip}/config/rsNetFloodProfileTable/{profile_name}

bdos_profiles:
  - "BDOS_Profile_5"
  - "BDOS_Profile_6"
```
***Key Features:
- Profiles cannot be deleted if still associated with any dependent settings
- Module validates existence before deletion
- Order of deletion handled automatically
- Both names and indexes supported internally (no need to provide index)

###  Create DNS Profile 
```json
POST /mgmt/device/byip/10.105.192.32/config/rsDnsProtProfileTable/{profile_name}
{
            "rsDnsProtProfileName": "dns_profile_1",
            "rsDnsProtProfileDnsAStatus": "2",
            "rsDnsProtProfileDnsMxStatus": "2",
            "rsDnsProtProfileDnsPtrStatus": "2",
            "rsDnsProtProfileDnsAaaaStatus": "2",
            "rsDnsProtProfileDnsTextStatus": "2",
            "rsDnsProtProfileDnsSoaStatus": "2",
            "rsDnsProtProfileDnsNaptrStatus": "2",
            "rsDnsProtProfileDnsSrvStatus": "2",
            "rsDnsProtProfileDnsOtherStatus": "2",
            "rsDnsProtProfileExpectedQps": "1000",
            "rsDnsProtProfileDnsAQuota": "50",
            "rsDnsProtProfileDnsMxQuota": "20",
            "rsDnsProtProfileDnsPtrQuota": "12",
            "rsDnsProtProfileDnsAaaaQuota": "15",
            "rsDnsProtProfileDnsTextQuota": "2",
            "rsDnsProtProfileDnsSoaQuota": "1",
            "rsDnsProtProfileDnsNaptrQuota": "1",
            "rsDnsProtProfileDnsSrvQuota": "1",
            "rsDnsProtProfileDnsOtherQuota": "1",
            "rsDnsProtProfileAction": "1",
            "rsDnsProtProfileMaxAllowQps": "5000",
            "rsDnsProtProfileSigRateLimTarget": "0",
            "rsDnsProtProfileManualTriggerStatus": "2",
            "rsDnsProtProfileManualTriggerActThresh": "0",
            "rsDnsProtProfileManualTriggerTermThresh": "0",
            "rsDnsProtProfileManualTriggerMaxQpsTarget": "0",
            "rsDnsProtProfilePacketReportStatus": "1",
            "rsDnsProtProfileQueryNameMonitoringSensitivity": "1",
            "rsDnsProtProfileLearningSuppressionThreshold": "25",
            "rsDnsProtProfileFootprintStrictness": "1"
        }
# Note - If you enable manual trigger , you must disable all query.Also termination thresholds must be less than activation thresholds.
```
##### Edit BDoS Profile 
```json
PUT /mgmt/device/byip/10.105.192.32/config/rsDnsProtProfileTable/{profile_name}
{
            "rsDnsProtProfileName": "dns_profile_1",
            "rsDnsProtProfileDnsAStatus": "2",
            "rsDnsProtProfileDnsMxStatus": "2",
            "rsDnsProtProfileDnsPtrStatus": "2",
            "rsDnsProtProfileDnsAaaaStatus": "2",
            "rsDnsProtProfileDnsTextStatus": "2",
            "rsDnsProtProfileDnsSoaStatus": "2",
            "rsDnsProtProfileDnsNaptrStatus": "2",
            "rsDnsProtProfileDnsSrvStatus": "2",
            "rsDnsProtProfileDnsOtherStatus": "2",
            "rsDnsProtProfileExpectedQps": "1000",
            "rsDnsProtProfileDnsAQuota": "50",
            "rsDnsProtProfileDnsMxQuota": "20",
            "rsDnsProtProfileDnsPtrQuota": "12",
            "rsDnsProtProfileDnsAaaaQuota": "15",
            "rsDnsProtProfileDnsTextQuota": "2",
            "rsDnsProtProfileDnsSoaQuota": "1",
            "rsDnsProtProfileDnsNaptrQuota": "1",
            "rsDnsProtProfileDnsSrvQuota": "1",
            "rsDnsProtProfileDnsOtherQuota": "1",
            "rsDnsProtProfileAction": "1",
            "rsDnsProtProfileMaxAllowQps": "5000",
            "rsDnsProtProfileSigRateLimTarget": "0",
            "rsDnsProtProfileManualTriggerStatus": "2",
            "rsDnsProtProfileManualTriggerActThresh": "0",
            "rsDnsProtProfileManualTriggerTermThresh": "0",
            "rsDnsProtProfileManualTriggerMaxQpsTarget": "0",
            "rsDnsProtProfilePacketReportStatus": "1",
            "rsDnsProtProfileQueryNameMonitoringSensitivity": "1",
            "rsDnsProtProfileLearningSuppressionThreshold": "25",
            "rsDnsProtProfileFootprintStrictness": "1"
        }
```
Usage:
Call edit_dns_profile once per device, passing list of profiles to edit.
Each profile dict must include profile_name (mandatory) and any parameters to change

#### Get DNS Profile 
```json
GET /mgmt/device/byip/10.105.192.32/config/rsDnsProtProfileTable/{profile_name}

Response:
 {
    "msg": [
        "Device: 10.105.192.32",
        "DNS Profiles Found (2 entries):",
        "  Profile Name: dns_profile_1",
        "  --------------------------------------------------",
        "  Basic Configuration:",
        "      expected_qps                        4000",
        "      max_allow_qps                       5000",
        "      a_quota                             90",
        "      mx_quota                            45",
        "      ptr_quota                           45",
        "      aaaa_quota                          15",
        "      text_quota                          8",
        "      soa_quota                           2",
        "      naptr_quota                         2",
        "      srv_quota                           2",
        "      other_quota                         2",
        "      a_status                            enable",
        "      mx_status                           enable",
        "      ptr_status                          enable",
        "      aaaa_status                         enable",
        "      text_status                         enable",
        "      soa_status                          enable",
        "      naptr_status                        enable",
        "      srv_status                          enable",
        "      other_status                        enable",
        "      action                              block_and_report",
        "      manual_trigger                      disable",
        "      packet_report                       enable",
        "      packet_trace                        disable",
        "      subdomains_wl_learning              enable",
        "      footprint_strictness                medium",
        "      learning_suppression_threshold      25",
        "    --------------------------------------------------",
        ""
    ]
}
```
#Usage:-
#Call get_bdos_profile once per device
#filter_dns_profile_names: ["dns_profile_1"]
#Returns nested structure: profiles -> settings
#API mappings handled internally

### Delete DNS Profile
```yml
DELETE /mgmt/device/byip/{dp_ip}/config/rsDnsProtProfileTable/{profile_name}

bdos_profiles:
  - "DNS_Profile_5"
  - "DNS_Profile_6"
```
***Key Features:
- Profiles cannot be deleted if still associated with any dependent settings
- Module validates existence before deletion
- Order of deletion handled automatically


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