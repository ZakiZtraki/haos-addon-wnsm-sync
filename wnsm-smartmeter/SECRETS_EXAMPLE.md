# Using Home Assistant Secrets with Wiener Netze Smart Meter Add-on

This add-on supports Home Assistant's `secrets.yaml` file for secure credential management.

## Step-by-Step Setup

### 1. Edit your secrets.yaml file

Open your Home Assistant configuration directory and edit the `secrets.yaml` file:

**File location:** `/config/secrets.yaml`

```yaml
# Wiener Netze Smart Meter credentials
wnsm_username: "your-email@example.com"
wnsm_password: "your-secure-password"
wnsm_zp: "AT0030000000000000000000012345678"

# MQTT credentials (if using external MQTT broker)
mqtt_username: "your-mqtt-username"
mqtt_password: "your-mqtt-password"
mqtt_host: "192.168.1.100"

# Optional: aWATTar API key (for future cost calculation features)
awattar_api_key: "your-awattar-api-key"
```

### 2. Configure the add-on using secret references

In the add-on configuration tab, use the `!secret` syntax:

```yaml
WNSM_USERNAME: "!secret wnsm_username"
WNSM_PASSWORD: "!secret wnsm_password"
WNSM_ZP: "!secret wnsm_zp"
MQTT_HOST: "core-mosquitto"
MQTT_PORT: 1883
MQTT_USERNAME: "!secret mqtt_username"
MQTT_PASSWORD: "!secret mqtt_password"
MQTT_TOPIC: "smartmeter/energy/15min"
UPDATE_INTERVAL: 86400
HISTORY_DAYS: 7
```

### 3. Alternative: Mix secrets with direct values

You can mix secret references with direct configuration:

```yaml
# Use secrets for sensitive data
WNSM_USERNAME: "!secret wnsm_username"
WNSM_PASSWORD: "!secret wnsm_password"
WNSM_ZP: "!secret wnsm_zp"

# Use direct values for non-sensitive settings
MQTT_HOST: "core-mosquitto"
MQTT_PORT: 1883
MQTT_TOPIC: "smartmeter/energy/15min"
UPDATE_INTERVAL: 86400
HISTORY_DAYS: 7
DEBUG: false
```

## Benefits

✅ **Security**: Credentials are not visible in the add-on configuration UI  
✅ **Centralized**: All secrets in one place (`/config/secrets.yaml`)  
✅ **Reusable**: Same secrets can be used across multiple add-ons  
✅ **Version Control Safe**: Configuration files can be committed without exposing credentials  
✅ **Easy Management**: Update credentials in one place  

## Troubleshooting

### Secret not found error
If you see a warning like "Secret 'wnsm_username' not found in secrets.yaml":

1. Check that the secret name in `secrets.yaml` matches exactly
2. Ensure there are no typos in the secret name
3. Verify that `secrets.yaml` is in the correct location (`/config/secrets.yaml`)
4. Restart Home Assistant after editing `secrets.yaml`

### Syntax errors
- Secret references must be quoted: `"!secret secret_name"`
- Secret names can only contain letters, numbers, and underscores
- Make sure your `secrets.yaml` file has valid YAML syntax

### Testing your secrets
You can test if your secrets are loaded correctly by:

1. Checking the add-on logs for "Loaded X secrets from /config/secrets.yaml"
2. Looking for warnings about missing secrets
3. Verifying that the add-on starts successfully with your configuration

## Example Complete Configuration

**secrets.yaml:**
```yaml
# Wiener Netze credentials
wnsm_user: "john.doe@example.com"
wnsm_pass: "MySecurePassword123!"
wnsm_meter: "AT0030000000000000000000012345678"

# MQTT settings
mqtt_user: "homeassistant"
mqtt_pass: "mqtt_secure_password"
```

**Add-on configuration:**
```yaml
WNSM_USERNAME: "!secret wnsm_user"
WNSM_PASSWORD: "!secret wnsm_pass"
WNSM_ZP: "!secret wnsm_meter"
MQTT_HOST: "core-mosquitto"
MQTT_USERNAME: "!secret mqtt_user"
MQTT_PASSWORD: "!secret mqtt_pass"
MQTT_TOPIC: "smartmeter/energy/15min"
UPDATE_INTERVAL: 86400
HISTORY_DAYS: 1
```

This setup keeps your sensitive credentials secure while making configuration management easier!