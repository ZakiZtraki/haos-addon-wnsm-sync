# Wiener Netze Smartmeter Sync Add-on for Home Assistant

This Home Assistant add-on fetches 15-minute interval consumption data from the Wiener Netze Smart Meter portal and publishes it to Home Assistant via MQTT.

## Features
- Authenticates with Wiener Netze login using PKCE (Proof Key for Code Exchange)
- Retrieves Bewegungsdaten (quarter-hourly history)
- Publishes data to Home Assistant via MQTT
- Automatically creates sensors through MQTT discovery
- Supports the latest Wiener Netze API authentication methods (as of May 2025)
- Can be scheduled to run at custom intervals

## Add-ons

### Wiener Netze Smart Meter Integration

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FZakiZtraki%2Fhaos-addon-wnsm-sync)

This add-on synchronizes your Wiener Netze Smart Meter data to Home Assistant via MQTT.

## Installation

1. Click the button above to add this repository to your Home Assistant instance.
2. Navigate to the Add-on Store.
3. Find the "Wiener Netze Smart Meter" add-on and click it.
4. Click "Install".

## Configuration

The add-on requires the following configuration:

```yaml
WNSM_USERNAME: your_wiener_netze_username
WNSM_PASSWORD: your_wiener_netze_password
ZP: your_zaehlpunkt_number  # e.g., AT0010000000000000001000004392265
MQTT_HOST: core-mosquitto  # or your MQTT broker address
MQTT_PORT: 1883
MQTT_USERNAME: your_mqtt_username  # if required
MQTT_PASSWORD: your_mqtt_password  # if required
MQTT_TOPIC: smartmeter/energy/state
UPDATE_INTERVAL: 86400  # in seconds (default: 24 hours)
HISTORY_DAYS: 1  # number of days of historical data to fetch
USE_MOCK_DATA: false  # set to true for testing without real API access
```

### Advanced Configuration Options

```yaml
RETRY_COUNT: 3  # number of retry attempts for API calls
RETRY_DELAY: 10  # delay between retry attempts in seconds
DEBUG: false  # enable debug logging
```

### Mock Data Mode

If you're testing the add-on or don't have access to the Wiener Netze API, you can enable mock data mode:

1. Set `USE_MOCK_DATA: true` in your configuration
2. The add-on will generate simulated data instead of making real API calls
3. This is useful for development, testing, or demonstration purposes

When mock data mode is enabled, you'll see a warning in the logs indicating that simulated data is being used.

## Troubleshooting

If you encounter issues with the API connection:

1. Check your credentials (username, password, and Zählpunkt number)
2. Verify that your Wiener Netze account has access to the Smart Meter portal
3. Try enabling mock data mode temporarily to verify that the rest of the integration works
4. Check the add-on logs for detailed error messages

### Common Issues

- **Authentication failures**: Make sure your Wiener Netze username and password are correct
- **No data available**: Verify that your Zählpunkt (ZP) is correct and that your smart meter is activated
- **MQTT connection issues**: Check that your MQTT broker is running and accessible

## Technical Details

This add-on uses the [vienna-smartmeter](https://github.com/cretl/vienna-smartmeter) library with PKCE authentication support to communicate with the Wiener Netze API. PKCE (Proof Key for Code Exchange) is required by the Wiener Netze API since May 2025 for secure OAuth authentication.

# Fix for 15-Minute Delta Values Issue

## Problem Summary

The Wiener Netze Smart Meter add-on was incorrectly aggregating 15-minute energy consumption data into cumulative values instead of publishing individual 15-minute deltas. This caused Home Assistant to show a single large cumulative value (15-16000 kWh) instead of individual 15-minute consumption intervals.

## Root Cause

1. **Cumulative Sum Logic**: The main processing function was calculating running totals (`total += value_kwh`) instead of using individual delta values
2. **Wrong State Class**: MQTT discovery was configured with `state_class: total_increasing` which expects cumulative values
3. **Incorrect MQTT Payload**: Publishing cumulative sums instead of individual 15-minute consumption deltas

## Solution Implemented

### 1. Fixed Main Processing Logic (`main()` function)

**Before:**
```python
total = Decimal(0)
for entry in bewegungsdaten.get("values", []):
    value_kwh = Decimal(str(entry["wert"]))
    total += value_kwh  # ❌ Creating cumulative sum
    statistics.append({
        "start": ts.isoformat(),
        "sum": float(total),  # ❌ Cumulative value
        "state": float(value_kwh)
    })
```

**After:**
```python
for entry in bewegungsdaten.get("values", []):
    value_kwh = float(entry["wert"])  # ✅ Individual 15-min consumption
    statistics.append({
        "start": ts.isoformat(),
        "delta": value_kwh,  # ✅ Individual delta value
        "timestamp": ts.isoformat()
    })
```

### 2. Updated MQTT Publishing (`publish_mqtt_data()` function)

**Before:**
- Complex grouping and sampling logic
- Publishing cumulative sums
- Multiple topics per day

**After:**
- Simple iteration through all 15-minute intervals
- Publishing individual delta values
- Single topic with timestamp-based messages

**New MQTT Payload Format:**
```json
{
  "delta": 0.234,
  "timestamp": "2025-01-15T00:15:00+00:00"
}
```

### 3. Updated Home Assistant MQTT Discovery

**Before:**
```yaml
state_class: "total_increasing"  # ❌ For cumulative values
value_template: "{{ value_json.value }}"  # ❌ Wrong field
```

**After:**
```yaml
state_class: "measurement"  # ✅ For delta/interval values
value_template: "{{ value_json.delta }}"  # ✅ Extract delta field
name: "WNSM 15min Energy"  # ✅ Clear naming
```

## Expected Behavior After Fix

1. **Individual 15-minute intervals**: Each API response entry becomes a separate MQTT message
2. **Correct consumption values**: Values like 0.234 kWh per 15-minute interval instead of 15000+ kWh cumulative
3. **Home Assistant integration**: Sensor shows individual 15-minute consumption that can be:
   - Graphed over time
   - Summed for daily/monthly totals
   - Multiplied with aWATTar price sensor for cost calculation
4. **Energy Dashboard compatibility**: Can be added to HA Energy Dashboard for consumption tracking

## Files Modified

1. **`wnsm_sync/sync_bewegungsdaten_to_ha.py`**:
   - `main()` function: Fixed data processing logic
   - `publish_mqtt_data()` function: Simplified MQTT publishing
   - `publish_mqtt_discovery()` function: Updated HA discovery config

## Testing

Created `test_delta_fix.py` to verify:
- ✅ Correct delta value processing
- ✅ Proper MQTT payload format
- ✅ Valid Home Assistant discovery configuration
- ✅ All existing tests still pass

## Home Assistant Configuration

After the fix, configure your Home Assistant sensor like this:

```yaml
mqtt:
  sensor:
    - name: "WNSM 15min Energy"
      state_topic: "smartmeter/energy/15min"
      unit_of_measurement: "kWh"
      device_class: energy
      state_class: measurement
      value_template: "{{ value_json.delta }}"
      json_attributes_topic: "smartmeter/energy/15min"
      json_attributes_template: "{{ {'timestamp': value_json.timestamp} | tojson }}"
```

## Cost Calculation Integration

You can now create a template sensor to calculate costs:

```yaml
template:
  - sensor:
      - name: "Energy Cost 15min"
        unit_of_measurement: "€"
        device_class: monetary
        state_class: measurement
        state: >
          {{ (states('sensor.wnsm_15min_energy') | float) *
             (states('sensor.awattar_price_now') | float) }}
```

## Verification

To verify the fix works:

1. Check MQTT messages: Should see individual delta values (0.1-0.5 kWh range)
2. Check HA sensor history: Should show varying 15-minute intervals
3. Check Energy Dashboard: Should accumulate properly over time
4. Total daily consumption should match your actual usage

The fix ensures that instead of seeing one massive cumulative value, you'll see realistic 15-minute consumption intervals that Home Assistant can properly process and display.
