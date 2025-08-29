# DefensePro Configuration Builder - Developer Guide

**Technical documentation for developers working on the DefensePro Ansible modules**

## Architecture Overview

```
dp_config_builder/
├── playbooks/           # Ansible playbooks (orchestration layer)
├── plugins/
│   ├── modules/         # Custom Ansible modules (business logic)
│   └── module_utils/    # Shared utilities (RadwareCC, Logger)
├── vars/               # Configuration templates and user data
└── tasks/              # Reusable task fragments
```

## Module Architecture

### Core Components

1. **RadwareCC** (`plugins/module_utils/radware_cc.py`)
   - HTTP client with session management
   - Automatic re-authentication on 403 errors
   - Request/response logging and error handling

2. **Logger** (`plugins/module_utils/logger.py`)
   - Structured logging with verbosity levels
   - File-based logging with rotation

3. **Network Class Modules** (`plugins/modules/`)
   - CRUD operations for DefensePro network classes
   - Consistent parameter validation and error handling

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

## Module Development Pattern

### Standard Module Structure
```python
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        # Operation-specific parameters
    )
    
    result = dict(changed=False, response={})
    debug_info = {}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    # Extract provider and setup logging
    provider = module.params['provider']
    log_level = provider.get('log_level', 'disabled')
    from ansible.module_utils.logger import Logger
    logger = Logger(verbosity=log_level)
    
    try:
        # Initialize RadwareCC client
        cc = RadwareCC(provider['cc_ip'], provider['username'], 
                      provider['password'], log_level=log_level, logger=logger)
        
        if not module.check_mode:
            # Construct API request
            # Execute operation
            # Handle response
            pass
            
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        module.fail_json(msg=str(e), debug_info=debug_info, **result)
    
    result['debug_info'] = debug_info
    module.exit_json(**result)
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

## Error Handling

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

1. **Create Module** (`plugins/modules/new_operation.py`)
   - Follow the standard module pattern
   - Add proper documentation strings
   - Implement error handling

2. **Create Playbook** (`playbooks/new_operation.yml`)
   - Use external variable files
   - Include device locking/unlocking
   - Add descriptive loop labels

3. **Create Variables** (`vars/new_operation_vars.yml.example`)
   - Document all parameters
   - Provide usage examples
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
