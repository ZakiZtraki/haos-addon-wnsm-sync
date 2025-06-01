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