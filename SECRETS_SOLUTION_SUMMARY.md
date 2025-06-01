# Home Assistant Secrets Support - Final Solution

## Problem Solved

The initial implementation using `!secret` syntax in add-on configuration failed because Home Assistant's Supervisor validates add-on configurations **before** the add-on starts, and it doesn't recognize the `!secret` syntax in add-on options.json files.

**Error encountered:**
```
Failed to save add-on configuration, Unknown secret 'wnsm_username' in Wiener Netze Smartmeter Sync
```

## Solution Implemented

I've implemented a **Home Assistant-compatible secrets approach** that works within the Supervisor's validation system while still providing secure credential management.

### How It Works

#### Method 1: USE_SECRETS Mode (Recommended)
1. **Enable secrets mode** in add-on configuration: `USE_SECRETS: true`
2. **Leave credential fields empty** in the UI
3. **Store credentials in `/config/secrets.yaml`**
4. **Add-on automatically loads** credentials from secrets file

#### Method 2: Automatic Fallback
1. **Leave USE_SECRETS disabled** (`false`)
2. **Leave credential fields empty** in the UI  
3. **Add-on automatically detects missing credentials** and loads from secrets.yaml

### Configuration Examples

#### secrets.yaml
```yaml
# Wiener Netze credentials
wnsm_username: "your-email@example.com"
wnsm_password: "your-secure-password"
wnsm_zp: "AT0030000000000000000000012345678"

# MQTT credentials (optional)
mqtt_username: "homeassistant"
mqtt_password: "mqtt-password"
```

#### Add-on Configuration (Method 1)
```yaml
USE_SECRETS: true
WNSM_USERNAME: ""
WNSM_PASSWORD: ""
ZP: ""
MQTT_HOST: "core-mosquitto"
MQTT_USERNAME: ""
MQTT_PASSWORD: ""
```

#### Add-on Configuration (Method 2)
```yaml
USE_SECRETS: false
WNSM_USERNAME: ""  # Will auto-load from secrets.yaml
WNSM_PASSWORD: ""  # Will auto-load from secrets.yaml
ZP: ""             # Will auto-load from secrets.yaml
MQTT_HOST: "core-mosquitto"
```

## Technical Implementation

### New Configuration Schema
- Added `USE_SECRETS` boolean option to config.json
- Made credential fields optional (`str?` instead of `str`)
- Maintains backward compatibility with direct values

### Enhanced Configuration Loading
1. **Load options.json** and check `USE_SECRETS` flag
2. **Detect missing credentials** automatically
3. **Load secrets.yaml** when needed
4. **Apply secret mappings** with multiple name variations
5. **Fall back to environment variables** if needed

### Secret Name Mappings
The add-on supports multiple naming conventions:

| Configuration | Secret Names (in order of preference) |
|---------------|---------------------------------------|
| USERNAME | `wnsm_username`, `username` |
| PASSWORD | `wnsm_password`, `password` |
| ZP | `wnsm_zp`, `zp`, `wnsm_meter`, `meter` |
| MQTT_USERNAME | `mqtt_username`, `mqtt_user` |
| MQTT_PASSWORD | `mqtt_password`, `mqtt_pass` |

## Benefits

✅ **No Validation Errors**: Works with Home Assistant's add-on validation  
✅ **Secure**: Credentials not visible in add-on configuration UI  
✅ **Flexible**: Multiple ways to use secrets (explicit mode or automatic)  
✅ **Compatible**: Supports various secret naming conventions  
✅ **Backward Compatible**: Existing configurations continue to work  
✅ **User Friendly**: Simple checkbox to enable secrets mode  

## User Instructions

### For New Users (Recommended)
1. Add credentials to `/config/secrets.yaml`
2. Enable `USE_SECRETS: true` in add-on configuration
3. Leave all credential fields empty
4. Save configuration - no validation errors!

### For Existing Users
1. **Option A**: Enable `USE_SECRETS: true` and clear credential fields
2. **Option B**: Leave `USE_SECRETS: false` and clear credential fields (automatic fallback)
3. **Option C**: Keep using direct values (no change needed)

## Files Modified

### Core Implementation
- **config.json**: Added `USE_SECRETS` option, made credentials optional
- **sync_bewegungsdaten_to_ha.py**: Enhanced configuration loading logic
- **requirements.txt**: Added PyYAML dependency

### Documentation
- **DOCS.md**: Updated with new secrets usage instructions
- **SECRETS_EXAMPLE.md**: Comprehensive examples for new approach

### Testing
- **test_new_secrets_approach.py**: Full test suite for new functionality
- All existing tests continue to pass

## Migration Path

### From Previous !secret Implementation
If you tried the previous `!secret` approach and got validation errors:

1. **Remove** any `!secret` references from add-on configuration
2. **Add** your credentials to `/config/secrets.yaml` (if not already there)
3. **Enable** `USE_SECRETS: true` in add-on configuration
4. **Clear** all credential fields in the UI
5. **Save** - should work without validation errors

### From Direct Configuration
If you're currently using direct values in the add-on configuration:

1. **Add** credentials to `/config/secrets.yaml`
2. **Enable** `USE_SECRETS: true`
3. **Clear** credential fields in add-on configuration
4. **Save** - credentials will be loaded from secrets file

## Security Advantages

- **UI Security**: Credentials never visible in add-on configuration interface
- **Log Security**: Sensitive values are masked in logs
- **File Security**: Secrets centralized in one protected file
- **Version Control**: Configuration files can be safely committed
- **Audit Trail**: Clear logging of which secrets are being used

This solution provides the security benefits of secrets management while working seamlessly with Home Assistant's add-on system!