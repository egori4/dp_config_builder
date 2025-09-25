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
# See what network classes exist
ansible-playbook playbooks/get_network_class.yml

# Create new network classes
ansible-playbook playbooks/create_network_class.yml

# Edit existing network classes  
ansible-playbook playbooks/edit_network_class.yml

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

# Get all BDoS profiles from devices
ansible-playbook playbooks/get_bdos_profile.yml

# Create new BDoS profiles
ansible-playbook playbooks/create_bdos_profile.yml

# Edit existing BDoS profiles
ansible-playbook playbooks/edit_bdos_profile.yml

# Delete BDoS profiles
ansible-playbook playbooks/delete_bdos_profile.yml

# Get all OOS profiles from devices
ansible-playbook playbooks/get_oos_profile.yml

# Create new OOS profiles
ansible-playbook playbooks/create_oos_profile.yml

# Edit existing OOS profiles
ansible-playbook playbooks/edit_oos_profile.yml

# Delete OOS profiles
ansible-playbook playbooks/delete_oos_profile.yml

# See what HTTPS profiles exist
ansible-playbook playbooks/get_https_profile.yml

# Create new HTTPS profiles
ansible-playbook playbooks/create_https_profile.yml

# Edit existing HTTPS profiles
ansible-playbook playbooks/edit_https_profile.yml

# Delete HTTPS profiles
ansible-playbook playbooks/delete_https_profile.yml
# Get all DNS profiles from devices
ansible-playbook playbooks/get_dns_profile.yml

# Create new DNS profiles
ansible-playbook playbooks/create_dns_profile.yml

# Edit existing DNS profiles
ansible-playbook playbooks/edit_dns_profile.yml

# Delete DNS profiles
ansible-playbook playbooks/delete_dns_profile.yml

# Get all SSL objects from devices
ansible-playbook playbooks/get_ssl_object.yml

# Create new SSL objects
ansible-playbook playbooks/create_ssl_object.yml

# Edit existing SSL objects
ansible-playbook playbooks/edit_ssl_object.yml

# Delete SSL objects
ansible-playbook playbooks/delete_ssl_object.yml

# Create security policies with orchestration (includes network classes, CL profiles, and policies)
ansible-playbook playbooks/create_security_policy.yml

# Edit existing security policies (partial updates and profile management)
ansible-playbook playbooks/edit_security_policy.yml

# Get Security policies and all profiles from devices
ansible-playbook playbooks/get_security_policy.yml

# Delete Security Policies(and optional corresponding profiles)
ansible-playbook playbooks/delete_security_policy.yml
```

## Common Workflows

### Workflow 1: Create New Network Classes
```bash
# 1. Edit your requirements
nano vars/create_vars.yml

# 2. Test first (dry run)
ansible-playbook --check playbooks/create_network_class.yml

# 3. Apply changes
ansible-playbook playbooks/create_network_class.yml
```

### Workflow 2: Modify Existing Networks
```bash
# 1. See current state
ansible-playbook playbooks/get_network_class.yml

# 2. Define your changes
nano vars/edit_vars.yml

# 3. Test first (dry run)
ansible-playbook --check playbooks/edit_network_class.yml

# 4. Apply changes
ansible-playbook playbooks/edit_network_class.yml
```

### Workflow 3: Clean Up Networks
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

### Workflow 4: Create Connection Limit Profiles
```bash
# 1. Configure protections and profiles
nano vars/create_vars.yml

# 2. Test first (dry run)
ansible-playbook --check playbooks/create_cl_profiles.yml

# 3. Apply configuration
ansible-playbook playbooks/create_cl_profiles.yml

# Alternative: Use with check mode for testing
ansible-playbook playbooks/create_cl_profiles.yml --check
```

#### Workflow 4a: Create Protections Only (Skip Profiles)
```bash
# 1. Edit create_vars.yml - define cl_protections section, comment out cl_profiles
nano vars/create_vars.yml

# 2. Test and apply
ansible-playbook --check playbooks/create_cl_profiles.yml
ansible-playbook playbooks/create_cl_profiles.yml
```

#### Workflow 4b: Create Profiles Only (Use Existing Protections)
```bash
# 1. Edit create_vars.yml - comment out cl_protections, define cl_profiles with existing names
nano vars/create_vars.yml

# 2. Test and apply  
ansible-playbook --check playbooks/create_cl_profiles.yml
ansible-playbook playbooks/create_cl_profiles.yml
```

### Workflow 5: Edit Connection Limit Protections
```bash
# 1. Identify existing protections (check DefensePro UI for protection indexes)
# Protection indexes start from 450001 and increment

# 2. Configure your changes (only specify what you want to change)
nano vars/edit_vars.yml

# 3. Test first (dry run) - shows exactly what will change
ansible-playbook --check playbooks/edit_cl_protections.yml

# 4. Apply changes
ansible-playbook playbooks/edit_cl_protections.yml
```

**Note**: For editing, you only need to specify the parameters you want to change. All other parameters remain unchanged on the device.

**Usage patterns**:
- **Create new protections + profiles**: Define both `cl_protections` and `cl_profiles` sections
- **Create protections only**: Define `cl_protections` section, skip `cl_profiles` section
- **Use only existing protections**: Skip `cl_protections`, define only `cl_profiles` with existing protection names
- **Mixed approach**: Create some new protections, reference some existing ones in the same profile

### Workflow 6: Get Network Classes with Filtering
```bash
# 1. See all network classes on devices
ansible-playbook playbooks/get_network_class.yml

# 2. Filter by specific class names (edit get_vars.yml first)
nano vars/get_vars.yml  # Set filter_class_names: ["web_servers", "db_servers"]
ansible-playbook playbooks/get_network_class.yml

# 3. Reset to show all classes
nano vars/get_vars.yml  # Set filter_class_names: []
ansible-playbook playbooks/get_network_class.yml
```

**Note**: The get operation shows network classes with detailed breakdown including IP ranges and group information. You can filter by class names or show all classes.

### Workflow 7: Get Connection Limit Profiles
```bash
# 1. See all profiles and protections on devices
ansible-playbook playbooks/get_cl_profiles.yml

# 2. Filter by specific profile names (edit get_vars.yml first)
nano vars/get_vars.yml  # Set filter_cl_profile_names: ["profile1", "profile2"]
ansible-playbook playbooks/get_cl_profiles.yml

# 3. Reset to show all profiles
nano vars/get_vars.yml  # Set filter_cl_profile_names: []
ansible-playbook playbooks/get_cl_profiles.yml
```

**Note**: The get operation shows profiles with their associated protections and all protection settings. You can filter by profile names or show all profiles.

### Workflow 8: Delete Connection Limit Profiles and Protections
```bash
# 1. Identify what to delete (get current state first)
ansible-playbook playbooks/get_cl_profiles.yml

# 2. Configure your deletions
nano vars/delete_vars.yml

# 3. Test first (dry run) - shows exactly what will be deleted
ansible-playbook --check playbooks/delete_cl_profiles.yml

# The check mode will show:
# - Profile Operations: Which protections will be removed from which profiles
# - Protection Deletions: Which protections will be deleted entirely (with their indexes)
# - Validation: Both names and indexes are validated against current device state
# - Status indicators: NOT FOUND for protections/indexes that don't exist on the device

# 4. Apply deletions
ansible-playbook playbooks/delete_cl_profiles.yml
```

**Important Rules for Deletion**:
- **Profile deletions**: Remove protections from profiles (profile auto-deleted when last protection removed)
- **Protection deletions**: Delete protections entirely (protection must not be in any profile)
- **Order matters**: Profile deletions are processed before protection deletions
- **Dependencies**: Cannot delete protection if it's still associated with any profile
- **Preview mode**: Use `--check` flag to see exactly what would be deleted before applying changes

**Usage patterns**:
- **Remove from profiles only**: Define `cl_profile_deletions` section, skip `cl_protection_deletions`
- **Delete protections only**: Skip `cl_profile_deletions`, define `cl_protection_deletions` with standalone protections
- **Complete cleanup**: Define both sections - remove from profiles first, then delete protections


### Workflow 9 :Create New BDoS Profiles
```bash
# 1. Define your BDoS profiles
nano vars/create_vars.yml

# 2. Test first (dry run)
ansible-playbook --check playbooks/create_bdos_profile.yml

# 3. Apply configuration
ansible-playbook playbooks/create_bdos_profile.yml
```

### Workflow 9a :Edit Existing BDoS Profile
```bash
nano vars/edit_vars.yml
ansible-playbook --check playbooks/edit_bdos_profile.yml
ansible-playbook playbooks/edit_bdos_profile.yml
```

#### workflow 9b :Get BDoS Profile
```bash
ansible-playbook playbooks/get_bdos_profile.yml
```

#### workflow 9c : Delete BDoS Profile
```bash
nano vars/delete_vars.yml
ansible-playbook --check playbooks/delete_bdos_profile.yml
ansible-playbook playbooks/delete_bdos_profile.yml
```

### Workflow 10 : Create New DNS Profiles

# 1. Define your DNS profiles
```bash
nano vars/create_vars.yml
```
# 2. Test first (dry run)
```bash
ansible-playbook --check playbooks/create_dns_profile.yml
```
# 3. Apply configuration
```bash
ansible-playbook playbooks/create_dns_profile.yml
```
### Workflow 10a : Edit Existing DNS Profile
```bash
nano vars/edit_vars.yml
ansible-playbook --check playbooks/edit_dns_profile.yml
ansible-playbook playbooks/edit_dns_profile.yml
```
### Workflow 10b : Get DNS Profile
```bash
ansible-playbook playbooks/get_dns_profile.yml
```
### Workflow 10c : Delete DNS Profile
```bash
nano vars/delete_vars.yml
ansible-playbook --check playbooks/delete_dns_profile.yml
ansible-playbook playbooks/delete_dns_profile.yml
```

### Workflow 11 : Create New OOS Profiles

# 1.Define your OOS profiles
```bash
nano vars/create_vars.yml
```
# 2. Test first (dry run)
```bash
ansible-playbook --check playbooks/create_oos_profile.yml
```
# 3.Apply configuration
```bash
ansible-playbook playbooks/create_oos_profile.yml
```
### Workflow 11b : Get OOS Profile
```bash
ansible-playbook playbooks/get_oos_profile.yml
```
### Workflow 11c : Delete OOS Profile
```bash
nano vars/delete_vars.yml
ansible-playbook --check playbooks/delete_oos_profile.yml
ansible-playbook playbooks/delete_oos_profile.yml
```

### Workflow 12 : Create New  SSL Object

# 1.Define your SSL Object
```bash
nano vars/create_vars.yml
```
# 2. Test first (dry run)
```bash
ansible-playbook --check playbooks/create_ssl_object.yml
```
# 3.Apply configuration
```bash
ansible-playbook playbooks/create_ssl_object.yml
```
### Workflow 12a : Get SSL Object
```bash
ansible-playbook playbooks/get_ssl_object.yml
```
### Workflow 12b : Delete SSL Object
```bash
nano vars/delete_vars.yml
ansible-playbook --check playbooks/delete_ssl_object.yml
ansible-playbook playbooks/delete_ssl_object.yml
```
### Workflow 12c :Edit Existing SSL Object
```bash
nano vars/edit_vars.yml
ansible-playbook --check playbooks/edit_ssl_object.yml
ansible-playbook playbooks/edit_ssl_object.yml
```

### Workflow 13 : Create New HTTPS Profiles

# 1.Define your HTTPS profiles
```bash
nano vars/create_vars.yml
```
# 2. Test first (dry run)
```bash
ansble-playbook --check playbooks/create_https_profile.yml
```
# 3.Apply configuration
```bash
ansible-playbook playbooks/create_https_profile.yml
```
### Workflow 13b : Get HTTPS Profile
```bash
ansible-playbook playbooks/get_https_profile.yml
```
### Workflow 13c : Delete HTTPS Profile
```bash
nano vars/delete_vars.yml
ansible-playbook --check playbooks/delete_https_profile.yml
ansible-playbook playbooks/delete_https_profile.yml
```

### Workflow 14: Create Security Policies with Profile Bindings

```bash
# 1. Configure your orchestration settings  
nano vars/create_vars.yml

# Edit the security_policy_config section:
security_policy_config:
  create_network_classes: true    # Create network classes first
  create_cl_profiles: true        # Create CL profiles next  
  create_security_policies: true  # Create security policies last

# 2. Configure your security policies
# Add policies to the security_policies section with profile bindings

# 3. Test orchestration plan (preview mode)
ansible-playbook --check playbooks/create_security_policy.yml

# 4. Execute full orchestration
ansible-playbook playbooks/create_security_policy.yml
```

**Security Policy Features**:
- **Unified orchestration**: Creates profiles and security policies in sequence
- **Profile binding**: Binds protection profiles to policies
- **Flexible control**: Enable/disable each creation stage independently
- **Existing resource support**: Use existing profiles without recreating them

**Common scenarios**:
- **Full setup**: Enable all flags to create everything from scratch
- **Policies only**: Disable network and profile creation, use existing resources
- **Partial creation**: Mix and match what gets created vs. using existing resources

### Workflow 15: Apply DefensePro Policy Updates
```bash
# Option A: Automatic policy updates (during orchestration)
# 1. Enable automatic policy application in create_vars.yml
security_policy_config:
  apply_policies_after_creation: true  # Automatically apply policies after creation

# 2. Run orchestration - policies will be applied automatically
ansible-playbook playbooks/create_security_policy.yml

# Option B: Manual policy updates (standalone)
# 1. Configure target devices in update_vars.yml
nano vars/update_vars.yml  # Set target_devices list

# 2. Run the standalone policy update playbook
ansible-playbook playbooks/update_policies.yml

# Option C: Override target devices (alternative to editing vars file)
ansible-playbook playbooks/update_policies.yml -e "target_devices=['10.105.192.32','10.105.192.33']"
```

**Policy Update Features**:
- **Automatic integration**: Policies applied automatically during orchestration
- **Manual control**: Standalone playbook for manual policy updates using `vars/update_vars.yml`
- **Conditional execution**: Orchestration playbook "create_security_policy.yml" skip policy updates when controlled centrally
- **Safety confirmation**: Optional interactive prompts to prevent accidental updates
- **Per-device processing**: Updates applied individually with proper locking



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

### Connection Limit Profiles - Complete Configuration Reference

**Important**: Both `cl_protections` and `cl_profiles` sections are completely optional. You can define one, another or both, based on your needs.

#### Creating Connection Limit Protections (ALL Supported Parameters)
```yaml
# OPTIONAL: Protection subprofiles (only define if creating new ones)
cl_protections:
  - name: "cl_prot_comprehensive_example"        # MANDATORY: Protection name
    protocol: "tcp"                              # OPTIONAL: tcp, udp (default: tcp)
    threshold: "100"                             # OPTIONAL: Connection threshold (default: "50")
    app_port_group: "https"                      # OPTIONAL: http, https, dns, ftp, smtp, imap, custom port, or "" for all (default: "")
    tracking_type: "src_ip"                      # OPTIONAL: src_ip, dst_ip, src_and_dest_ip, dst_ip_and_port (default: dst_ip)
    action: "drop"                               # OPTIONAL: drop, report_only (default: drop)
    packet_report: "enable"                      # OPTIONAL: enable, disable (default: disable)
    protection_type: "cps"                       # OPTIONAL: cps, concurrent_connections (default: cps)
    index: 450001                                # OPTIONAL: 0 or 450001+ (default: 0)

  # Minimal example (only mandatory parameter)
  - name: "cl_prot_minimal"                      # MANDATORY: Only this is required
    # All other parameters will use defaults

  # Custom index example
  - name: "cl_prot_custom_index"
    protocol: "udp"
    threshold: "200"
    index: 450002                                # Custom index
```

#### Editing Connection Limit Protections (Partial Updates)
```yaml
# Edit existing protections - ONLY specify what you want to change
edit_cl_protections:
  - protection_index: 450001                    # MANDATORY: Must specify which protection to edit
    protection_name: "Updated Protection"        # OPTIONAL: Change name only
    
  - protection_index: 450002                    # MANDATORY: Another protection to edit
    threshold: "500"                            # OPTIONAL: Change threshold only
    action: "report_only"                       # OPTIONAL: Change action only
    # All other parameters remain unchanged
    
  - protection_index: 450003                    # MANDATORY: Edit multiple parameters
    protocol: "udp"                             # OPTIONAL: Change protocol
    threshold: "300"                            # OPTIONAL: Change threshold
    tracking_type: "dst_ip_and_port"           # OPTIONAL: Change tracking
    packet_report: "disable"                   # OPTIONAL: Change reporting
    # Other parameters remain unchanged
```

#### Getting Connection Limit Profiles and Protections
```yaml
# Get all profiles and protections from devices
# No configuration needed - just run the playbook
ansible-playbook playbooks/get_cl_profiles.yml

# Filter by specific profile names (configure in get_vars.yml)
filter_cl_profile_names: ["profile1", "profile2"]  # Show only these profiles
# filter_cl_profile_names: []                      # Show all profiles (default)
```

#### Deleting Connection Limit Profiles and Protections
```yaml
# OPTIONAL: Remove protections from profiles (without deleting protection itself)
cl_profile_deletions:
  - profile_name: "profile_to_modify"
    protections:
      - "protection1"
      - "protection2"

# OPTIONAL: Delete protections entirely (protection must not be in any profile)
cl_protection_deletions:
  - protections_to_delete:
      - "standalone_protection"      # Delete by name (module looks up index)
      - "another_protection"         # Delete by name (module looks up index)
      - "old_protection"             # Delete by name (module looks up index)
      - 450001                       # Delete by index directly
      - 450002                       # Delete by index directly

# Important: Both sections are optional - define based on your needs
# Order: Profile deletions processed first, then protection deletions
```

**Parameter Reference for Connection Limit Protections**:

| Parameter | Status | Options | Default | Description |
|-----------|--------|---------|---------|-------------|
| `name` | **MANDATORY** | Any string | - | Protection name (create only) |
| `protection_index` | **MANDATORY** | Integer | - | Index to edit (edit only) |
| `protocol` | OPTIONAL | tcp, udp | tcp | Network protocol |
| `threshold` | OPTIONAL | "number" | "50" | Connection limit threshold |
| `app_port_group` | OPTIONAL | http, https, dns, ftp, smtp, imap, custom port, "" | "" | Application port filter |
| `tracking_type` | OPTIONAL | src_ip, dst_ip, src_and_dest_ip, dst_ip_and_port | dst_ip | Traffic tracking method |
| `action` | OPTIONAL | drop, report_only | drop | Action when threshold exceeded |
| `packet_report` | OPTIONAL | enable, disable | disable | Detailed packet reporting |
| `protection_type` | OPTIONAL | cps, concurrent_connections | cps | Detection type |
| `index` | OPTIONAL | 0 or 450001+ | 0 | Creation index |

**Key Points for Editing**:
-  **Partial Updates**: Only specify parameters you want to change
-  **Unchanged Values**: Unspecified parameters keep their current values
-  **Flexible**: Change one parameter or many in a single operation

#### Connection Limit Profiles (Optional Section)
```yaml
# OPTIONAL: Profiles (can reference existing or newly created protections)
cl_profiles:
  - name: "web_server_limits"                   # MANDATORY: Profile name
    protections:                                # MANDATORY: List of protections
      - "cl_prot_tcp_limit"                     # Will be created above
      - "existing_protection"                   # Already exists on DefensePro
      
  - name: "database_limits"                     # Another profile example
    protections:
      - "cl_prot_comprehensive_example"         # Reference created protection
      - "legacy_protection_on_device"           # Reference existing protection
```

**Profile Configuration Notes**:
-  **name**: MANDATORY - Unique profile name
-  **protections**: MANDATORY - List of protection names to include
-  **Mixed References**: Can combine newly created and existing protections
-  **Flexible**: Create profiles with any combination of protections
#### Usage Pattern Examples
```yaml
# Example 1: Create new protections + profiles (comprehensive)
cl_protections:
  - name: "web_protection"
    protocol: "tcp"
    threshold: "100"
    app_port_group: "https"
    tracking_type: "src_ip"
    action: "drop"
    index: 450001
  - name: "api_protection"
    protocol: "tcp"
    threshold: "500"
    tracking_type: "dst_ip_and_port"
    action: "report_only"
    index: 450002

cl_profiles:
  - name: "web_security_profile"
    protections:
      - "web_protection"      # Newly created
      - "api_protection"      # Newly created

# Example 2: Use only existing protections (skip cl_protections entirely)
cl_profiles:
  - name: "profile_with_existing"
    protections:
      - "protection_already_on_device"
      - "another_existing_protection"

# Example 3: Mixed approach (some new, some existing)
cl_protections:
  - name: "new_custom_protection"
    protocol: "udp"
    threshold: "200"
    index: 450003

cl_profiles:
  - name: "mixed_profile"
    protections:
      - "new_custom_protection"      # Newly created above
      - "legacy_protection"          # Already exists on device
```


### Create BDOS Profile configuration ###
```yaml
# OPTIONAL: Define BDoS profiles (only define if creating new ones)
bdos_profiles:
  - name: "bdos_profile_5"           # MANDATORY: Profile name
    state: "enable"                              # OPTIONAL: enable, disable (default: enable)
    params:
      action: "block_and_report"                 # OPTIONAL: report_only, block_and_report (default: block_and_report)
      syn_flood: "enable"                        # OPTIONAL: enable, disable (default: disable)
      udp_flood: "enable"                        # OPTIONAL: enable, disable (default: disable)
      igmp_flood: "enable"                       # OPTIONAL: enable, disable (default: disable)
      icmp_flood: "enable"                       # OPTIONAL: enable, disable (default: disable)
      tcp_ack_fin_flood: "enable"                # OPTIONAL: enable, disable (default: disable)
      tcp_rst_flood: "enable"                    # OPTIONAL: enable, disable (default: disable)
      tcp_syn_ack_flood: "enable"                # OPTIONAL: enable, disable (default: disable)
      tcp_frag_flood: "enable"                   # OPTIONAL: enable, disable (default: disable)
      udp_frag_flood: "enable"                   # OPTIONAL: enable, disable (default: disable)

      inbound_traffic: 1000000                   # Mandatory
      outbound_traffic: 500000                   # Mandatory
      tcp_in_quota: 80                           # OPTIONAL: 0–100 (% share)
      udp_in_quota: 50
      icmp_in_quota: 10
      igmp_in_quota: 50
      tcp_out_quota: 80
      udp_out_quota: 50
      icmp_out_quota: 10
      igmp_out_quota: 50

      transparent_optimization: "enable"         # OPTIONAL: enable, disable (default: disable)
      packet_report: "enable"                    # OPTIONAL: enable, disable (default: disable)
      burst_attack: "disable"                    # OPTIONAL: enable, disable (default: disable)
      maximum_interval_between_bursts: 60        # OPTIONAL: 1–60 minutes (default: 10)
      learning_suppression_threshold: 10         # OPTIONAL: 0–50 (default: 0)
      footprint_strictness: "medium"             # OPTIONAL: low, medium, high (default: low)
      bdos_rate_limit: "user_defined"            # OPTIONAL: disable, normal_edge, suspect_edge, user_defined (default: disable)
      user_defined_rate_limit: 500               # OPTIONAL: 0–4000 (default: 0)
      udp_ packet_rate_detection_sensitivit: low # OPTIONAL: Ignore or Disable,low, medium, high      
      user_defined_rate_limit_unit: "mbps"       # OPTIONAL: kbps, mbps, gbps (default: mbps)
      adv_udp_detection: "enable"                # OPTIONAL: enable, disable (default: disable)

  # Minimal example (only mandatory parameter)
  - name: "bdos_profile5"                         # MANDATORY
    # All other parameters use defaults



### Editing BDoS Profiles (Partial Updates) ###
```yaml
# Edit existing BDoS profiles - ONLY specify what you want to change
bdos_profiles:
  - profile_name: "bdos_comprehensive_example"   # MANDATORY: must specify which profile to edit
    params:
      action: "report_only"                      # OPTIONAL: Change action only

  - profile_name: "bdos_minimal"                 # MANDATORY
    params:
      inbound_traffic: 2000000                   # OPTIONAL: Change threshold
      outbound_traffic: 1000000                  # OPTIONAL: Change threshold

  - profile_name: "bdos_custom"                  # MANDATORY
    params:
      syn_flood: "disable"                       # OPTIONAL: Disable SYN flood detection
      udp_flood: "enable"                        # OPTIONAL: Enable UDP flood detection
      footprint_strictness: "high"               # OPTIONAL: Update detection sensitivity
    # All other parameters remain unchanged
```


#### Get BDoS Profiles  ####
```yaml
# Get all BDoS profiles from devices
# No configuration needed - just run the playbook
ansible-playbook playbooks/get_bdos_profile.yml
# Filter by specific profile names (configure in get_vars.yml)
filter_bdos_profile_names: ["BDOS_Profile_5", "BDOS_Profile_6"]  # Show only these profiles
# filter_bdos_profile_names: []                                # Show all profiles (default)

#### Delete BDoS Profiles  ####
```yaml
# Delete BDoS profiles by name
bdos_profiles:
  - "BDOS_Profile_5"
  - "BDOS_Profile_6"
```

#### Bdos profile Notes:

*** name ***: MANDATORY – Unique profile name.
*** state ***: Optional – enable or disable (default: enable).
*** action ***: Required – choose between report_only or block_and_report.
*** Flood toggles (syn_flood, udp_flood, etc.) ***: Enable/disable specific protocol flood detection.
*** Traffic limits (inbound/outbound) ***: Mandatory; define baseline traffic thresholds (1–1342177280).
*** Quota values ***: Define % share of traffic per protocol (0–100).
*** Rate limiting ***: Select predefined (normal_edge, suspect_edge) or user_defined with unit and value.
*** Advanced controls ***: Includes burst attack detection, suppression threshold, footprint strictness, and advanced UDP detection.
*** Control flags ***: create_bdos_profiles can be toggled independently to enable/disable orchestration.

#### Create DNS Profiles  ####
```yaml
# Define DNS profiles to create on each device
# Configure DNS profiles in `vars/create_vars.yml`:
# OPTIONAL: DNS profiles (only define if creating new ones)
create_dns_profiles:
  - name: "dns_profile_1"               # MANDATORY: Profile name
    state: "enable"                     # OPTIONAL: enable, disable (default: enable)
    params:
      action: "block_&_report"        # OPTIONAL: report_only, block_&_report (default: block_and_report)
      expected_qps: 1000                # OPTIONAL: 0–400000000 (default: 0)
      max_allow_qps: 5000               # OPTIONAL: 0–400000000 (default: 0)
      sig_rate_lim_target: 10                 # Range: 0-100 in %

      # Manual trigger configuration
      manual_trigger: "disable"         # OPTIONAL: enable, disable (default: disable)
      manual_trigger_act_thresh: 2000   # OPTIONAL: ≥ termination threshold
      manual_trigger_term_thresh: 1000  # OPTIONAL
      manual_trigger_max_qps_target: 3000
      manual_trigger_act_period: 30     # OPTIONAL: seconds
      manual_trigger_term_period: 15
      manual_trigger_escalate_period: 60
    
      # Logging / debug
      packet_report: "enable"           # OPTIONAL: enable, disable (default: disable)

      # Advanced detection
      learning_suppression_threshold: 10 # OPTIONAL: 0–100 (default: 0)
      footprint_strictness: "medium"    # OPTIONAL: low, medium, high (default: low)

      # Record quotas
      a_quota: 100                      # OPTIONAL
      mx_quota: 50
      ptr_quota: 20
      aaaa_quota: 50
      text_quota: 10
      soa_quota: 5
      naptr_quota: 5
      srv_quota: 10
      other_quota: 5

      # Record statuses (enable/disable)
      a_status: "enable"
      mx_status: "enable"
      ptr_status: "enable"
      aaaa_status: "enable"
      text_status: "enable"
      soa_status: "enable"
      naptr_status: "disable"
      srv_status: "disable"
      other_status: "enable"

  # Note - If you enable manual trigger , you must disable all query.Also termination thresholds must be less than activation thresholds.
  # Minimal example (only mandatory parameter)
  - name: "dns_profile_1"         # MANDATORY
    # All other parameters use defaults
```
### Editing DNS Profiles (Partial Updates)
```yml

# Edit existing DNS profiles - ONLY specify what you want to change
# Note - If you are editing QPS and quota same time then you have to run the playbook twice. 
edit_dns_profiles:
  - name: "dns_profile_10"                      # MANDATORY: must specify which profile to edit
    params:
      action: "report_only"                     # OPTIONAL: report_only, block_&_report
      expected_qps: 2000                        # OPTIONAL: Update expected QPS
      max_allow_qps: 8000                       # OPTIONAL: Update max QPS
      sig_rate_lim_target: 10                   # Range: 0-100 in %
      a_status: "disable"                       # OPTIONAL: Disable A record protection
      mx_status: "enable"                       # OPTIONAL: Enable MX record protection
      footprint_strictness: "high"              # OPTIONAL: Update detection sensitivity
      packet_report: "disable"                  # OPTIONAL: Change logging/reporting
      a_in_quota: 40                            # OPTIONAL: % share for A record (0–100)
      mx_in_quota: 30                           # OPTIONAL: % share for MX record (0–100)
      cname_in_quota: 20                        # OPTIONAL: % share for CNAME record (0–100)
      other_in_quota: 10                        # OPTIONAL: % share for other records (0–100)
      a_out_quota: 35                           # OPTIONAL: % share for outbound A record (0–100)
      mx_out_quota: 25                          # OPTIONAL: % share for outbound MX record (0–100)
      cname_out_quota: 15                      # OPTIONAL: % share for outbound CNAME record (0–100)
      other_out_quota: 5                        # OPTIONAL: % share for other outbound (0–100)
```
### Get DNS Profiles
```yml
# Get all DNS profiles from devices
# No configuration needed - just run the playbook
ansible-playbook playbooks/get_dns_profile.yml

filter_dns_profile_names: ["dns_profile_1"]
```
### Delete DNS Profiles
```yml
# Delete DNS profiles by name
delete_dns_profiles:
  - "dns_profile_1"
  - "dns_profile_2"
```
### DNS Profile Notes:

*** name ***: MANDATORY – Unique profile name
*** state ***: Optional – enable or disable (default: enable)
*** action ***: REQUIRED – choose between report_only or block_and_report
*** Query-type toggles ***: Optional – enable/disable detection for specific query types (a_query, aaaa_query, mx_query, ns_query, ptr_query, soa_query, srv_query, txt_query)
*** Traffic limits ***: MANDATORY – baseline DNS query thresholds in queries per second (inbound_qps, outbound_qps)
*** Quota values ***: Optional – percentage share per query type (0–100%)
*** Rate limiting ***: Optional – select predefined (normal_edge, suspect_edge) or user_defined with unit and value
*** Advanced controls ***: Optional – includes NXDOMAIN handling, malformed query detection, response rate limiting, protocol anomaly checks, footprint strictness, learning suppression thresholds
*** Control flags ***: Use to enable/disable each creation stage independently

### Create OOS Profiles ###
# Define OOS profiles to create on each device
# Configure OOS profiles in `vars/create_vars.yml`:
# OPTIONAL: OOS profiles (only define if creating new ones)

```yaml
oos_profiles:
  - name: "oos_profile_1"            # MANDATORY: Profile name
    state: "enable"                  # OPTIONAL: enable, disable (default: enable)
    params:
      action: "block_and_report"     # OPTIONAL: report_only, block_and_report (default: block_and-report)
      syn_ack_allow: "enable"        # OPTIONAL: enable, disable (default: enable)
      packet_report: "enable"        # OPTIONAL: enable, disable (default: disable)
      risk: "medium"                 # OPTIONAL: low, medium, high (default: medium)
      act_threshold: 1000            # OPTIONAL: action threshold
      term_threshold: 500            # OPTIONAL: termination threshold
      idle_state: "enable"           # OPTIONAL: enable, disable (default: disable)
      idle_state_bandwidth_threshold: 1000  # OPTIONAL: threshold for idle state
      idle_state_timer: 30           # OPTIONAL: seconds for idle timeout
```
  # Minimal example (only mandatory parameter)
  - name: "oos_profile_2"             # MANDATORY
    # All other parameters use defaults

### Editing OOS Profiles (Partial Updates)
```yaml
# Edit existing OOS profiles - ONLY specify what you want to change
oos_profiles:
  - name: "oos_profile_1"     # MANDATORY: must specify which profile to edit
    params:
      action: "report_only"           # OPTIONAL: report_only, block_and_report
      syn_ack_allow: "disable"        # OPTIONAL: enable, disable
      packet_report: "disable"        # OPTIONAL: enable, disable
      risk: "high"                    # OPTIONAL: low, medium, high
      act_threshold: 1500             # OPTIONAL: activation threshold
      term_threshold: 800             # OPTIONAL: termination threshold
      idle_state: "disable"           # OPTIONAL: enable, disable
      idle_state_bandwidth_threshold: 1000  # OPTIONAL: threshold for idle state
      idle_state_timer: 30           # OPTIONAL: seconds for idle timeout
```

### Get OOS Profiles
# Get all OOS profiles from devices
# No configuration needed - just run the playbook
```yaml
ansible-playbook playbooks/get_oos_profile.yml

oos_profiles:
  - "oos_profile_1"
  - "oos_profile_2"                  # Show all profiles (default)
```

### Delete OOS Profiles

# Delete OOS profiles by name
```yaml
oos_profiles:
  - name: "oos_profile_1"
  - name: "oos_profile_2"
```

### Notes for OOS Profiles

*** name ***: MANDATORY – Unique profile name.
*** state ***: Optional – enable or disable (default: enable).
*** action ***: REQUIRED – choose between report_only or block_and_report.
*** syn_ack_allow ***: Optional – enable/disable SYN-ACK handling.
*** packet_report ***: Optional – enable/disable packet logging.
*** risk ***: Optional – low, medium, or high risk profile.
*** Thresholds ***
    act_threshold: activation threshold.
    term_threshold: termination threshold.
    Idle state controls:
    idle_state: enable/disable.
    idle_state_bandwidth_threshold: threshold for idle state.
    idle_state_timer: seconds for idle timeout.
    Control flags: Use to enable/disable each stage independently.

### Create SSL Object ###
# Define ssl object to create on each device
# Configure ssl object in `vars/create_vars.yml`:
```yml
create_ssl_objects:
  - ssl_object_name: "server1"         # MANDATORY: SSL object name
    ssl_object_profile: "enable"       # OPTIONAL: enable, disable (default: enable)
    ip_address: "155.1.102.7"          # MANDATORY: Device IP
    Port: 443                           # OPTIONAL: Port (default: 443)
    add_certificate: "radware"         # OPTIONAL: Certificate to add
    remove_certificate: ""             # OPTIONAL: Certificate to remove
    front_sslv3: "disable"             # OPTIONAL: enable, disable (default: disable)
    front_tls1.0: "disable"            # OPTIONAL: enable, disable (default: disable)
    front_tls1.1: "enable"             # OPTIONAL: enable, disable (default: enable)
    front_tls1.2: "enable"             # OPTIONAL: enable, disable (default: enable)
    front_tls1.3: "enable"             # OPTIONAL: enable, disable (default: enable)
    cipher_suite: "enable"             # OPTIONAL: enable, disable (default: enable)
    front_user_cipher: ""              # OPTIONAL: User-defined cipher
    bk_end_decrypt: "enable"           # OPTIONAL: enable, disable (default: enable)
    bk_end_sslv3: "disable"            # OPTIONAL: enable, disable (default: disable)
    bk_end_tls1.0: "disable"           # OPTIONAL: enable, disable (default: disable)
    bk_end_tls1.1: "enable"            # OPTIONAL: enable, disable (default: enable)
    bk_end_tls1.2: "enable"            # OPTIONAL: enable, disable (default: enable)
    bk_end_tls1.3: "enable"            # OPTIONAL: enable, disable (default: enable)
    bk_cipher: "enable"                # OPTIONAL: enable, disable (default: enable)
    bk_user_cipher: ""                 # OPTIONAL: User-defined cipher
    bk_end_port: 443                   # OPTIONAL: Backend port (default: 443)
```
### Edit SSL Object ###
# Edit existing DNS profiles - ONLY specify what you want to change
# Edit ssl object in `vars/edit_vars.yml`:
```yml
edit_ssl_objects:
  - ssl_object_name: "server1"         # MANDATORY: SSL object name
    ssl_object_profile: "enable"       # OPTIONAL: enable, disable (default: enable)
    ip_address: "155.1.102.7"          # MANDATORY: Device IP
    Port: 443                           # OPTIONAL: Port (default: 443)
    add_certificate: "radware"         # OPTIONAL: Certificate to add
    remove_certificate: ""             # OPTIONAL: Certificate to remove
    front_sslv3: "disable"             # OPTIONAL: enable, disable (default: disable)
    front_tls1.0: "disable"            # OPTIONAL: enable, disable (default: disable)
    front_tls1.1: "enable"             # OPTIONAL: enable, disable (default: enable)
    front_tls1.2: "enable"             # OPTIONAL: enable, disable (default: enable)
    front_tls1.3: "enable"             # OPTIONAL: enable, disable (default: enable)
    cipher_suite: "enable"             # OPTIONAL: enable, disable (default: enable)
    front_user_cipher: ""              # OPTIONAL: User-defined cipher
    bk_end_decrypt: "enable"           # OPTIONAL: enable, disable (default: enable)
    bk_end_sslv3: "disable"            # OPTIONAL: enable, disable (default: disable)
    bk_end_tls1.0: "disable"           # OPTIONAL: enable, disable (default: disable)
    bk_end_tls1.1: "enable"            # OPTIONAL: enable, disable (default: enable)
    bk_end_tls1.2: "enable"            # OPTIONAL: enable, disable (default: enable)
    bk_end_tls1.3: "enable"            # OPTIONAL: enable, disable (default: enable)
    bk_cipher: "enable"                # OPTIONAL: enable, disable (default: enable)
    bk_user_cipher: ""                 # OPTIONAL: User-defined cipher
    bk_end_port: 443                   # OPTIONAL: Backend port (default: 443)
  ```

### Get SSL Object
# Get all SSL Object from devices
# No configuration needed - just run the playbook
ansible-playbook playbooks/get_ssl_object.yml
```yaml
filter_ssl_object_names: ["server1", "server2"]

```

### Delete OOS Profiles

# Delete ssl object by name
```yaml
delete_ssl_objects:
  - name: server1
  - name: server2
```
Notes for SSL Objects

*** ssl_object_name ***: MANDATORY – Unique name for the SSL object.
*** ssl_object_profile ***: Optional – enable or disable the SSL object (default: enable).
*** IP_Address ***: MANDATORY – The IP address for the SSL object.
*** Port ***: Optional – Port number (default: 443).
*** add_certificate ***: Optional – Name of certificate to add.
*** remove_certificate ***: Optional – Name of certificate to remove.
*** Frontend Protocols ***: Optional – Enable/disable SSL/TLS versions on the frontend.
# front_sslv3
# front_tls1.0
# front_tls1.1
# front_tls1.2
# front_tls1.3
*** Cipher Controls (Frontend) ***: Optional – Enable/disable cipher support.
# cipher_suite
# front_user_cipher
*** Backend Decryption ***: Optional – Enable/disable backend SSL decryption.
# bk_end_decrypt
*** Backend Protocols ***: Optional – Enable/disable SSL/TLS versions on the backend.
# bk_end_sslv3
# bk_end_tls1.0
# bk_end_tls1.1
# bk_end_tls1.2
# bk_end_tls1.3
*** Cipher Controls (Backend) ***: Optional – Enable/disable cipher support.
# bk_cipher
# bk_user_cipher
*** bk_end_port ***: Optional – Backend port number (default: same as frontend port).

# Notes:
# Frontend and backend protocol/cipher flags can be used independently to enable/disable stages.
# Certificates must exist on the device before adding to SSL objects.
# Ensure IP address and port are correct; invalid values will result in API errors.


### Create HTTPS Profiles ###
```yaml
# Define HTTPS profiles to create on each device
# Configure HTTPS profiles in `vars/create_vars.yml`:
# OPTIONAL: HTTPS profiles (only define if creating new ones)


create_https_profiles:
  - name: "https_profile_1"
    params:
      action: "report_only"   # report_only,block_and_report
      rate_limit: "2000"      # Packets per Second per Source
      http_authentication_on_suspect_sources: "enable"  # enable, disable
      http_authentication_on_all_sources: "enable"      # enable, disable
      rate_limit_status: "enable"                       # enable, disable
      packet_report: "disable"                          # enable, disable
      full_session_decryption: "disable"                # enable, disable
      #challenge_method: "javascript"                   # javascript, redirect_302



#Minimal example (only mandatory parameter)
 create_https_profiles:
  - name: "http_profile_2"
    params:
      action: "report_only"
    # All other parameters use defaults
```
### Editing HTTPS Profiles (Partial Updates)
```yaml
# Edit existing HTTPS profiles - ONLY specify what you want to change
edit_https_profiles:
  - name: "http_profile_1"
    params:
      action: "report_only"                             # report_only,block_and_report
      rate_limit: "2000"                                # Packets per Second per Source
      http_authentication_on_suspect_sources: "enable"  # enable, disable
      http_authentication_on_all_sources: "enable"      # enable, disable
      rate_limit_status: "enable"                       # enable, disable
      packet_report: "disable"                          # enable, disable
      full_session_decryption: "disable"                # enable, disable
      #challenge_method: "javascript"                   # javascript, redirect_302, SSL Decryption and Encryption should be enabled on the DP for this to work
```

### Get HTTPS Profiles
```yaml
# Get all HTTPS profiles from devices
# No configuration needed - just run the playbook
ansible-playbook playbooks/get_https_profile.yml

filter_https_profile_names: ["http_profile_3"]

```

### Delete HTTP Profiles

```yaml
delete_https_profiles:
  - "https_profile_1"
  - "https_profile_2"                  # Show all profiles (default)
```

### Security Policy Configuration

**Security Policy Configuration Notes**:
- **policy_name**: MANDATORY - Unique policy name
- **src_network, dst_network**: MANDATORY - Network class names (use "any" for any network)
- **direction**: MANDATORY - Traffic direction to match
- **Profile bindings**: All optional - leave empty string for no binding
- **Control flags**: Use to enable/disable each creation stage independently

Configure security policies with profile bindings in `vars/create_vars.yml`:

```yaml
# Orchestration control flags
security_policy_config:
  create_network_classes: true     # Create network classes first
  create_cl_profiles: true         # Create CL profiles next
  create_security_policies: true   # Create security policies last

# Security policies with profile bindings
security_policies:
  - policy_name: "web_server_protection"
    state: "enable"                        # enable, disable
    action: "block_and_report"                        # block_and_report, report_only
    src_network: "any"                     # Source network class
    dst_network: "web_servers"             # Destination network class  
    direction: "oneway"                    # oneway, twoway
    priority: "100"                        # Policy priority (lower = higher precedence)
    packet_reporting_status: "enable"      # enable, disable
    
    # Profile bindings (all optional)
    connection_limit_profile: "web_cl_profile"
    bdos_profile: "default_netflood_profile"
    syn_protection_profile: "default_syn_profile"
    dns_flood_profile: ""                  # Empty = no binding
    https_flood_profile: ""
    traffic_filters_profile: ""
    signature_protection_profile: "web_appsec_profile"
    ert_attackers_feed_profile: ""
    geo_feed_profile: ""
    out_of_state_profile: ""
```
### Editing Security Policies

Modify existing security policies using partial updates in `vars/edit_vars.yml`:

```yaml
# Target DefensePro devices
dp_ip:
  - "10.105.192.32"

# Security policies to edit
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
    dns_flood_profile: ""                   # DNS flood profile name
    https_flood_profile: ""                 # HTTPS flood profile name
    traffic_filters_profile: ""             # Traffic filters profile name
    signature_protection_profile: "app_sec" # Application security profile name
    ert_attackers_feed_profile: ""          # ERT attackers feed profile name
    geo_feed_profile: ""                    # Geo feed profile name
    out_of_state_profile: ""                # Out of state profile name

  # Edit another policy - minimal changes
  - policy_name: "database_protection"
    action: "report_only"                   # Change to monitoring mode
    connection_limit_profile: ""            # Remove connection limit protection
```

**Run the playbook**:
```bash
# Preview changes (check mode)
ansible-playbook -i inventory.ini playbooks/edit_security_policy.yml --check

# Execute changes
ansible-playbook -i inventory.ini playbooks/edit_security_policy.yml
```

**Security Policy Editing Notes**:
- **policy_name**: MANDATORY - Must be an existing security policy name
- **Partial Updates**: Only specify parameters you want to change - unspecified parameters remain unchanged
- **Profile Detachment**: Use empty string ("") to remove profile bindings
- **Profile Attachment**: Specify profile name to attach/change binding  
- **Preview Mode**: Use `--check` flag to see planned changes before execution
- **Control Flags**: Device locking can be skipped with `skip_device_lock: true` in vars

### Deleting Security Policies

Remove security policies with optional profile cleanup using `vars/delete_vars.yml`:

```yaml
# Target DefensePro devices
dp_ip:
  - "10.105.192.32"

# Security policies to delete
delete_security_policies:
  - policy_name: "test_security_policy"     # MANDATORY: Policy name to delete
    deletion_mode: "policy_only"            # OPTIONAL: policy_only | policy_and_profiles
  
  - policy_name: "old_security_policy"     # MANDATORY: Policy name to delete  
    deletion_mode: "policy_and_profiles"    # OPTIONAL: Advanced cleanup mode
    
  # deletion_mode defaults to "policy_only" if not specified
  - policy_name: "another_policy"           # Uses default safe deletion mode
```

**Deletion Modes**:

1. **`policy_only` (default)**:
   - Safe deletion - only removes the security policy
   - Associated profiles remain available for other policies
   - Use for most deletion scenarios

2. **`policy_and_profiles` (advanced)**:
   - May remove associated profiles if no longer used by other policies
   - Use with caution - may affect other policies
   - Only use when certain about profile cleanup requirements

**Usage Examples**:
```bash
# Delete policies with preview mode (recommended first step)
ansible-playbook playbooks/delete_security_policy.yml --check

# Delete policies (actual execution)
ansible-playbook playbooks/delete_security_policy.yml

# Delete with verbose output
ansible-playbook playbooks/delete_security_policy.yml -v
```

**Security Policy Deletion Notes**:
- **policy_name**: MANDATORY - Must be an existing security policy name
- **deletion_mode**: OPTIONAL - Defaults to "policy_only" for safety
- **Safe Default**: Always use "policy_only" unless certain about profile cleanup needs
- **Preview Mode**: Use `--check` flag to see planned deletions before execution
- **Batch Processing**: Multiple policies can be deleted in a single operation
- **Profile Safety**: "policy_only" mode preserves profiles for other policies to use
- **Advanced Cleanup**: "policy_and_profiles" mode should only be used when profiles are policy-specific

**Recommended Workflow**:
1. Use preview mode first: `ansible-playbook playbooks/delete_security_policy.yml --check`
2. Review planned deletions carefully
3. For shared environments, prefer "policy_only" mode
4. For standalone policies with unique profiles, consider "policy_and_profiles" mode
5. Execute deletion: `ansible-playbook playbooks/delete_security_policy.yml`



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
ansible-playbook playbooks/get_network_class.yml
```

###  **Test Before Applying**
```bash
ansible-playbook --check playbooks/edit_network_class.yml
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
ansible-playbook playbooks/get_network_class.yml > backup_$(date +%Y%m%d).log
```

###  **Use Descriptive Names**
```yaml
netclasses:
  - name: "web_servers_dmz"      # Good: Clear purpose
    # vs
  - name: "net1"                 # Bad: Unclear
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