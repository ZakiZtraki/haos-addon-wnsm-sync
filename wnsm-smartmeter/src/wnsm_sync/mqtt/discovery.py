"""Home Assistant MQTT Discovery integration."""

import logging
from typing import Dict, Any

from ..config.loader import WNSMConfig

logger = logging.getLogger(__name__)


class HomeAssistantDiscovery:
    """Manages Home Assistant MQTT Discovery configuration."""
    
    def __init__(self, config: WNSMConfig):
        """Initialize discovery manager.
        
        Args:
            config: WNSM configuration object
        """
        self.config = config
    
    def create_energy_sensor_config(self) -> Dict[str, Any]:
        """Create MQTT discovery configuration for energy sensor.
        
        Returns:
            Dictionary containing topic and config for discovery
        """
        # Generate unique sensor name based on Zählpunkt
        sensor_name = f"wnsm_energy_{self.config.zp[-8:]}"  # Last 8 digits of ZP
        
        # Discovery topic follows HA convention
        discovery_topic = f"homeassistant/sensor/{sensor_name}/config"
        
        # Base topic for sensor data
        state_topic = f"{self.config.mqtt_topic}/15min"
        
        # Sensor configuration
        sensor_config = {
            "name": "WNSM 15min Energy",
            "object_id": sensor_name,  # This controls the entity_id
            "unique_id": sensor_name,
            "state_topic": state_topic,
            "unit_of_measurement": "kWh",
            "device_class": "energy",
            "state_class": "measurement",
            "value_template": "{{ value_json.delta }}",
            "json_attributes_topic": state_topic,
            "json_attributes_template": "{{ {'timestamp': value_json.timestamp, 'quality': value_json.quality} | tojson }}",
            "icon": "mdi:flash",
            "device": {
                "identifiers": [f"wnsm_{self.config.zp}"],
                "name": f"Wiener Netze Smart Meter {self.config.zp[-8:]}",
                "model": "Smart Meter",
                "manufacturer": "Wiener Netze",
                "sw_version": "1.0.0"
            },
            "availability": {
                "topic": f"{self.config.mqtt_topic}/availability",
                "payload_available": "online",
                "payload_not_available": "offline"
            }
        }
        
        return {
            "topic": discovery_topic,
            "config": sensor_config
        }
    
    def create_total_sensor_config(self) -> Dict[str, Any]:
        """Create MQTT discovery configuration for daily total sensor.
        
        Returns:
            Dictionary containing topic and config for discovery
        """
        # Generate unique sensor name
        sensor_name = f"wnsm_daily_total_{self.config.zp[-8:]}"
        
        # Discovery topic
        discovery_topic = f"homeassistant/sensor/{sensor_name}/config"
        
        # State topic
        state_topic = f"{self.config.mqtt_topic}/daily_total"
        
        # Sensor configuration
        sensor_config = {
            "name": "WNSM Daily Total",
            "object_id": sensor_name,  # This controls the entity_id
            "unique_id": sensor_name,
            "state_topic": state_topic,
            "unit_of_measurement": "kWh",
            "device_class": "energy",
            "state_class": "total_increasing",
            "value_template": "{{ value_json.total }}",
            "json_attributes_topic": state_topic,
            "json_attributes_template": "{{ {'date': value_json.date, 'reading_count': value_json.reading_count} | tojson }}",
            "icon": "mdi:counter",
            "device": {
                "identifiers": [f"wnsm_{self.config.zp}"],
                "name": f"Wiener Netze Smart Meter {self.config.zp[-8:]}",
                "model": "Smart Meter",
                "manufacturer": "Wiener Netze",
                "sw_version": "1.0.0"
            },
            "availability": {
                "topic": f"{self.config.mqtt_topic}/availability",
                "payload_available": "online",
                "payload_not_available": "offline"
            }
        }
        
        return {
            "topic": discovery_topic,
            "config": sensor_config
        }
    
    def create_status_sensor_config(self) -> Dict[str, Any]:
        """Create MQTT discovery configuration for sync status sensor.
        
        Returns:
            Dictionary containing topic and config for discovery
        """
        # Generate unique sensor name
        sensor_name = f"wnsm_sync_status_{self.config.zp[-8:]}"
        
        # Discovery topic
        discovery_topic = f"homeassistant/sensor/{sensor_name}/config"
        
        # State topic
        state_topic = f"{self.config.mqtt_topic}/status"
        
        # Sensor configuration
        sensor_config = {
            "name": "WNSM Sync Status",
            "object_id": sensor_name,  # This controls the entity_id
            "unique_id": sensor_name,
            "state_topic": state_topic,
            "value_template": "{{ value_json.status }}",
            "json_attributes_topic": state_topic,
            "json_attributes_template": "{{ {'last_sync': value_json.last_sync, 'next_sync': value_json.next_sync, 'error': value_json.error} | tojson }}",
            "icon": "mdi:sync",
            "device": {
                "identifiers": [f"wnsm_{self.config.zp}"],
                "name": f"Wiener Netze Smart Meter {self.config.zp[-8:]}",
                "model": "Smart Meter",
                "manufacturer": "Wiener Netze",
                "sw_version": "1.0.0"
            }
        }
        
        return {
            "topic": discovery_topic,
            "config": sensor_config
        }
    
    def get_all_discovery_configs(self) -> list[Dict[str, Any]]:
        """Get all discovery configurations.
        
        Returns:
            List of discovery configuration dictionaries
        """
        return [
            self.create_energy_sensor_config(),
            self.create_total_sensor_config(),
            self.create_status_sensor_config()
        ]