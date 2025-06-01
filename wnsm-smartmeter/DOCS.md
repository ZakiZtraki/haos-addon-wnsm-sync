# Wiener Netze Smart Meter Add-on

This add-on integrates your Wiener Netze Smart Meter data with Home Assistant via MQTT.

## Features

- Fetches 15-minute interval energy consumption data from Wiener Netze Smart Meter
- Publishes data to Home Assistant via MQTT
- Automatically creates sensors in Home Assistant through MQTT discovery
- Supports the latest Wiener Netze API authentication methods

## Configuration

### Required parameters:

| Parameter | Description |
|-----------|-------------|
| WNSM_USERNAME | Your Wiener Netze portal username |
| WNSM_PASSWORD | Your Wiener Netze portal password |
| ZP | Your Zählpunkt (meter point number) |

### Using Home Assistant Secrets

This add-on supports Home Assistant's `secrets.yaml` file for storing sensitive information. Instead of entering credentials directly in the add-on configuration, you can store them securely in your secrets file.

#### Step 1: Add secrets to your `secrets.yaml` file

Edit your Home Assistant `secrets.yaml` file (located in `/config/secrets.yaml`) and add your credentials:

```yaml
# Wiener Netze Smart Meter credentials
wnsm_username: "your-username@example.com"
wnsm_password: "your-secure-password"
wnsm_zp: "AT0030000000000000000000012345678"

# MQTT credentials (if using external MQTT broker)
mqtt_username: "your-mqtt-username"
mqtt_password: "your-mqtt-password"
```

#### Step 2: Enable secrets mode in add-on configuration

In the add-on configuration tab, enable the "Use Secrets" option and leave the credential fields empty:

```yaml
USE_SECRETS: true
WNSM_USERNAME: ""
WNSM_PASSWORD: ""
ZP: ""
MQTT_HOST: "core-mosquitto"
MQTT_USERNAME: ""
MQTT_PASSWORD: ""
```

The add-on will automatically load credentials from your `secrets.yaml` file using these names:
- `wnsm_username` or `username` → WNSM_USERNAME
- `wnsm_password` or `password` → WNSM_PASSWORD  
- `wnsm_zp`, `zp`, `wnsm_meter`, or `meter` → ZP
- `mqtt_username` or `mqtt_user` → MQTT_USERNAME
- `mqtt_password` or `mqtt_pass` → MQTT_PASSWORD

#### Benefits of using secrets:

- **Centralized management**: All sensitive data in one place
- **Security**: Credentials not visible in add-on configuration UI
- **Reusability**: Same secrets can be used across multiple add-ons
- **Version control**: You can safely commit configuration files without exposing credentials

> 📖 **For detailed examples and troubleshooting**, see [SECRETS_EXAMPLE.md](SECRETS_EXAMPLE.md)

### MQTT parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| MQTT_HOST | MQTT broker hostname | core-mosquitto |
| MQTT_PORT | MQTT broker port | 1883 |
| MQTT_USERNAME | MQTT username | |
| MQTT_PASSWORD | MQTT password | |
| MQTT_TOPIC | MQTT topic for publishing data | smartmeter/energy/state |

### Other parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| UPDATE_INTERVAL | Data update interval in seconds | 86400 (24 hour) |
| HISTORY_DAYS | Number of days of historical data to fetch | 1 |
| RETRY_COUNT | Number of retry attempts for API calls | 3 |
| RETRY_DELAY | Delay between retry attempts in seconds | 10 |
| DEBUG | Enable debug logging | false |
| USE_MOCK_DATA | Use mock data instead of real API calls (for testing) | false |

## How it works

This add-on logs into your Wiener Netze portal, fetches your smart meter data, and publishes it to your Home Assistant MQTT broker. It automatically creates sensors in Home Assistant through MQTT discovery.

The add-on uses the [vienna-smartmeter](https://github.com/cretl/vienna-smartmeter) library (with PKCE authentication support) to communicate with the Wiener Netze API, ensuring compatibility with the latest API changes.

The data is updated according to the specified interval.

## Troubleshooting

If the add-on fails to start:
1. Check your credentials in the configuration
2. Verify that your MQTT broker is accessible
3. Check the add-on logs for detailed error messages

### Common issues:

- **Authentication failures**: Make sure your Wiener Netze username and password are correct
- **No data available**: Verify that your Zählpunkt (ZP) is correct and that your smart meter is activated
- **MQTT connection issues**: Check that your MQTT broker is running and accessible

## Technical details

This add-on uses the vienna-smartmeter Python library which implements the latest authentication methods required by the Wiener Netze API, including PKCE (Proof Key for Code Exchange) for secure OAuth authentication.