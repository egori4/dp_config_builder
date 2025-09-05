# DefensePro SYN Profile Module - Developer Guide

**Technical documentation for developers working on the DefensePro SYN Profile Ansible modules**

## Architecture Overview

```
dp_config_builder/
├── playbooks/           # Ansible playbooks (orchestration layer)
├── plugins/
│   ├── modules/         # Custom Ansible modules (business logic, e.g. create_syn_profile.py)
│   └── module_utils/    # Shared utilities (RadwareCC, Logger)
├── vars/                # Configuration templates and user data
└── tasks/               # Reusable task fragments
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

3. **SYN Profile Modules** (`plugins/modules/create_syn_profile.py`)
   - CRUD operations for DefensePro SYN profiles
   - Consistent parameter validation and error handling

## API Endpoints

### SYN Profile Management
| Operation | Method | Endpoint |
|-----------|--------|----------|
| **Create/Update** | POST | `/mgmt/device/byip/{dp_ip}/config/rsIDSSynProfilesTable/{profile_name}/{protection_name}` |

## Module Development Pattern

### Standard Module Structure
```python
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.radware_cc import RadwareCC

def run_module():
    module_args = dict(
        provider=dict(type='dict', required=True),
        dp_ip=dict(type='str', required=True),
        profile_name=dict(type='str', required=True),
        protection_name=dict(type='str', required=True),
        params=dict(type='dict', required=True),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    # ...existing code...
```

## Request/Response Patterns

### Create SYN Profile
```json
POST /mgmt/device/byip/10.105.192.33/config/rsIDSSynProfilesTable/Test1/TEST

{
    "rsIDSSynProfilesName": "Test1",
    "rsIDSSynProfileServiceName": "TEST",
    "rsIDSSynProfileType": 4
}
```

### Example Success Response
```json
{
    "status": "ok",
    "message": "SYN profile created successfully"
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

- Sessions stored in `./tmp/radware_cc_sessions/` or system temp
- Session lifetime: 600 seconds (configurable)
- Automatic cleanup of expired sessions

### Session File Format
```
session_{md5_hash}.pkl    # Pickled cookies
session_{md5_hash}.time   # Creation timestamp
```

## Logging

- Log levels: `disabled`, `info`, `debug`
- Log file: `playbooks/log/log_YYYYMMDD.log`
- Format: `[TIMESTAMP] [LEVEL] [MODULE] Message`

### Example Log Output
```
[2025-08-28 17:30:45] [INFO] [RadwareCC] Logging in to Radware CC at 10.105.193.3 as radware
[2025-08-28 17:30:45] [INFO] [create_syn_profile] Creating SYN profile Test1 with protection TEST
[2025-08-28 17:30:46] [DEBUG] [RadwareCC] Response status: 200
```

## Testing

### Unit Testing
```bash
python3 -m py_compile plugins/modules/create_syn_profile.py
```

### Integration Testing
```bash
ansible-playbook --check playbooks/create_syn_profile.yml
ansible-playbook playbooks/create_syn_profile.yml
```

## Extending the Modules

### Adding New Operations

1. **Create Module** (`plugins/modules/new_syn_operation.py`)
   - Follow the standard module pattern
   - Add proper documentation strings
   - Implement error handling

2. **Create Playbook** (`playbooks/new_syn_operation.yml`)
   - Use external variable files
   - Include device locking/unlocking

3. **Create Variables** (`vars/new_syn_operation_vars.yml.example`)
   - Document all parameters
   - Provide usage examples

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