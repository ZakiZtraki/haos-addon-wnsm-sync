# MQTT Message Retention Strategy

This document explains the MQTT message retention strategy used in the WNSM Sync project and provides guidance on when to retain messages.

## What is MQTT Message Retention?

When you publish an MQTT message with `retain=True`:
- The MQTT broker **stores the last message** on that topic
- **New subscribers** immediately receive the retained message when they subscribe
- The retained message **persists** until a new message is published or an empty retained message is sent

When `retain=False` (default):
- Messages are only delivered to **currently connected subscribers**
- **No message is stored** by the broker
- New subscribers **don't receive any historical messages**

## Current Retention Strategy

### ✅ Messages We RETAIN (`retain=True`)

#### 1. **Availability Messages** (`/availability`)
```python
# Example: homeassistant/wnsm_sync/availability
payload = "online" or "offline"
retain = True  # ✅ RETAINED
```

**Why retain?**
- New subscribers need to know if the service is currently running
- Critical for monitoring and alerting
- Low volume (only changes on start/stop)

#### 2. **Status Messages** (`/status`)
```python
# Example: homeassistant/wnsm_sync/status
payload = {
    "status": "success",
    "last_sync": "2025-01-15T10:30:00Z",
    "next_sync": "2025-01-15T11:30:00Z",
    "error": null
}
retain = True  # ✅ RETAINED
```

**Why retain?**
- Shows current sync status to new subscribers
- Important for troubleshooting
- Helps determine if service is working properly

#### 3. **Discovery Messages** (Home Assistant MQTT Discovery)
```python
# Example: homeassistant/sensor/wnsm_sync_15min/config
retain = True  # ✅ RETAINED (handled by HA discovery)
```

**Why retain?**
- Home Assistant needs discovery configs to be available
- Ensures sensors are recreated after HA restart

### ❌ Messages We DON'T RETAIN (`retain=False`)

#### 1. **Energy Data Messages** (`/15min`, `/daily_total`)
```python
# Example: homeassistant/wnsm_sync/15min
payload = {
    "delta": 0.234,
    "timestamp": "2025-01-15T10:15:00Z"
}
retain = False  # ❌ NOT RETAINED
```

**Why not retain?**
- **Time-sensitive data**: Each reading has a specific timestamp
- **High volume**: New reading every 15 minutes = 96 messages/day
- **Storage overhead**: Would accumulate thousands of retained messages
- **Confusion risk**: Old readings might be mistaken for current data
- **Home Assistant handles history**: HA stores time-series data in its database

## Implementation Details

### MQTT Client Configuration

The `MQTTClient.publish_message()` method now supports retention:

```python
def publish_message(
    self, 
    topic: str, 
    payload: Dict[str, Any], 
    retry_count: Optional[int] = None,
    retain: bool = False  # Default: don't retain
) -> bool:
```

### Usage Examples

```python
# Energy data - don't retain
self.mqtt_client.publish_message(
    f"{self.config.mqtt_topic}/15min", 
    reading.to_mqtt_payload()
    # retain=False (default)
)

# Status updates - retain
self.mqtt_client.publish_message(
    f"{self.config.mqtt_topic}/status", 
    status_payload,
    retain=True
)

# Availability - retain
publish.single(
    topic=f"{self.config.mqtt_topic}/availability",
    payload="online",
    retain=True
)
```

## Benefits of This Strategy

### 1. **Efficient Storage**
- Only retains essential status information
- Avoids accumulating thousands of energy readings
- Reduces MQTT broker memory usage

### 2. **Better User Experience**
- New Home Assistant instances immediately see current status
- No confusion from old energy readings
- Proper separation of real-time vs. historical data

### 3. **Monitoring & Troubleshooting**
- Service availability is always visible
- Last sync status helps with debugging
- Clear indication of service health

### 4. **Home Assistant Integration**
- Discovery configs are retained (standard practice)
- Energy data flows into HA's time-series database
- Status sensors show current state immediately

## MQTT Broker Storage Impact

### With Current Strategy:
```
Retained messages per service instance:
- 1 availability message
- 1 status message  
- ~4 discovery config messages
Total: ~6 retained messages
```

### If We Retained Everything:
```
Retained messages per service instance:
- 96 energy readings per day
- 365 days = 35,040 energy readings per year
- Plus status and availability messages
Total: 35,000+ retained messages per year
```

## Best Practices

### ✅ DO Retain:
- **Availability/status information**
- **Configuration data**
- **Current state information**
- **Low-frequency updates**

### ❌ DON'T Retain:
- **Time-series data** (energy readings, sensor values)
- **High-frequency updates**
- **Historical data**
- **Event notifications**

## Troubleshooting Retention Issues

### Problem: "I don't see the latest status in Home Assistant"
**Solution:** Check if status messages are being retained:
```bash
# Subscribe to see retained messages
mosquitto_sub -h your-mqtt-broker -t "homeassistant/wnsm_sync/status" -v
```

### Problem: "Too many retained messages in MQTT broker"
**Solution:** Clear retained messages for energy topics:
```bash
# Clear retained messages (send empty retained message)
mosquitto_pub -h your-mqtt-broker -t "homeassistant/wnsm_sync/15min" -r -n
```

### Problem: "Home Assistant sensors disappear after restart"
**Solution:** Ensure discovery messages are retained (should be automatic).

## Configuration Options

You can customize retention behavior by modifying the publish calls in:

- `src/wnsm_sync/core/sync.py` - Status and availability messages
- `src/wnsm_sync/mqtt/client.py` - General message publishing
- `src/wnsm_sync/mqtt/discovery.py` - Discovery message retention

## Monitoring Retention

To monitor what messages are retained:

```bash
# See all retained messages for your topic
mosquitto_sub -h your-mqtt-broker -t "homeassistant/wnsm_sync/+" -v --retained-only

# Check specific message retention
mosquitto_sub -h your-mqtt-broker -t "homeassistant/wnsm_sync/status" -v -C 1
```

This strategy balances functionality, performance, and storage efficiency while providing the best experience for Home Assistant integration.