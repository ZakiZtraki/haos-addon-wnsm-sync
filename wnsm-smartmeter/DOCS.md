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