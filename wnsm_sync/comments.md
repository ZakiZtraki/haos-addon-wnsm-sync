Ah, I understand better now. Since this is a daily sync that collects historical data (previous day's data points), we need to modify the MQTT configuration to properly handle this time-series data. Let me analyze the current implementation and suggest improvements.

Looking at the current code:
1. It fetches the previous day's data in 15-minute intervals
2. It publishes each reading to individual topics like `smartmeter/energy/state/2025-05-16T00:15`
3. It needs to ensure Home Assistant can properly process this historical data

Here's how we should modify the MQTT sensor configuration to handle this use case:

```python
# First, configure the MQTT sensor with proper timestamp handling
publish.single(
    topic="homeassistant/sensor/wnsm/energy/config",
    payload=json.dumps({
        "name": "Wiener Netze Smart Meter Sync",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit_of_measurement": "kWh",
        "state_topic": MQTT_TOPIC,
        "unique_id": "wnsm_sync",
        "value_template": "{{ value_json.value }}",
        "timestamp_template": "{{ value_json.timestamp }}",  # Add timestamp template
        "device": {
            "identifiers": ["wnsm_sync"],
            "name": "Wiener Netze Smart Meter Sync",
            "manufacturer": "Wiener Netze",
            "model": "Smart Meter"
        }
    }),
    hostname=MQTT_HOST,
    auth={
        "username": MQTT_USERNAME,
        "password": MQTT_PASSWORD
    },
    retain=True
)

# Then publish each reading with its timestamp
for s in statistics:
    payload = {
        "value": s["sum"],
        "timestamp": s["start"]  # This is already in ISO format
    }
    publish.single(
        topic=f"{MQTT_TOPIC}/{s['start'][:16]}",
        payload=json.dumps(payload),
        hostname=MQTT_HOST,
        auth={
            "username": MQTT_USERNAME,
            "password": MQTT_PASSWORD
        },
        retain=True
    )

# Finally, publish the latest state to the main topic
if statistics:
    latest = statistics[-1]
    publish.single(
        topic=MQTT_TOPIC,
        payload=json.dumps({
            "value": latest["sum"],
            "timestamp": latest["start"]
        }),
        hostname=MQTT_HOST,
        auth={
            "username": MQTT_USERNAME,
            "password": MQTT_PASSWORD
        },
        retain=True
    )
```

Key changes and explanations:

1. Added `timestamp_template` to the sensor configuration so Home Assistant knows when each reading was taken
2. Kept the individual timestamped topics for historical reference
3. Added a final publish to the main topic with the latest state
4. Ensured all messages include both value and timestamp

This configuration will:
- Create a proper energy sensor in Home Assistant
- Allow Home Assistant to process the historical data with correct timestamps
- Maintain the latest state between daily updates
- Keep the historical data points accessible

The sensor will show the most recent value but the historical data will be available for long-term statistics and graphs in Home Assistant. Since the addon runs once per day to import the previous day's data, this approach ensures all the historical data points are properly recorded while maintaining a current state for the sensor.

For additional robustness, you might want to add logging to track successful data imports:

```python
# Add after publishing all data
print(f"✅ Published {len(statistics)} readings for {yesterday.isoformat()}")
print(f"First reading: {statistics[0]['start']} = {statistics[0]['sum']} kWh")
print(f"Last reading: {statistics[-1]['start']} = {statistics[-1]['sum']} kWh")
```

This will help verify that the correct data is being imported each day and make troubleshooting easier if needed.