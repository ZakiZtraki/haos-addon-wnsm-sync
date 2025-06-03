#!/usr/bin/env python3
"""Tests for MQTT functionality."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from wnsm_sync.config.loader import WNSMConfig
from wnsm_sync.mqtt.client import MQTTClient
from wnsm_sync.mqtt.discovery import HomeAssistantDiscovery


def test_mqtt_host_parsing():
    """Test MQTT host parsing functionality."""
    
    # Test simple hostname
    config = WNSMConfig(
        wnsm_username="test",
        wnsm_password="test",
        zp="AT0010000000000000001000004392265",
        mqtt_host="localhost"
    )
    
    client = MQTTClient(config)
    assert client._hostname == "localhost"
    assert client._port == 1883
    
    # Test hostname with port
    config.mqtt_host = "localhost:1884"
    client = MQTTClient(config)
    assert client._hostname == "localhost"
    assert client._port == 1884
    
    # Test URL format
    config.mqtt_host = "mqtt://broker.example.com:1885"
    client = MQTTClient(config)
    assert client._hostname == "broker.example.com"
    assert client._port == 1885
    
    print("✅ MQTT host parsing works correctly")


def test_mqtt_auth_preparation():
    """Test MQTT authentication preparation."""
    
    # Test without auth
    config = WNSMConfig(
        wnsm_username="test",
        wnsm_password="test",
        zp="AT0010000000000000001000004392265",
        mqtt_host="localhost"
    )
    
    client = MQTTClient(config)
    assert client._auth is None
    
    # Test with auth
    config.mqtt_username = "mqtt_user"
    config.mqtt_password = "mqtt_pass"
    client = MQTTClient(config)
    
    assert client._auth is not None
    assert client._auth["username"] == "mqtt_user"
    assert client._auth["password"] == "mqtt_pass"
    
    print("✅ MQTT authentication preparation works correctly")


@patch('paho.mqtt.publish.single')
def test_mqtt_publish_message(mock_publish):
    """Test MQTT message publishing."""
    
    config = WNSMConfig(
        wnsm_username="test",
        wnsm_password="test",
        zp="AT0010000000000000001000004392265",
        mqtt_host="localhost"
    )
    
    client = MQTTClient(config)
    
    # Test successful publish
    mock_publish.return_value = None
    result = client.publish_message("test/topic", {"test": "data"})
    
    assert result == True
    mock_publish.assert_called_once()
    
    # Verify call arguments
    call_args = mock_publish.call_args
    assert call_args[1]["topic"] == "test/topic"
    assert '"test": "data"' in call_args[1]["payload"]
    assert call_args[1]["hostname"] == "localhost"
    assert call_args[1]["port"] == 1883
    
    print("✅ MQTT message publishing works correctly")


def test_home_assistant_discovery():
    """Test Home Assistant discovery configuration."""
    
    config = WNSMConfig(
        wnsm_username="test",
        wnsm_password="test",
        zp="AT0010000000000000001000004392265",
        mqtt_host="localhost",
        mqtt_topic="smartmeter/energy/state"
    )
    
    discovery = HomeAssistantDiscovery(config)
    
    # Test energy sensor config
    energy_config = discovery.create_energy_sensor_config()
    
    assert "topic" in energy_config
    assert "config" in energy_config
    
    config_data = energy_config["config"]
    assert config_data["device_class"] == "energy"
    assert config_data["state_class"] == "measurement"
    assert config_data["unit_of_measurement"] == "kWh"
    assert "{{ value_json.delta }}" in config_data["value_template"]
    
    # Test device information
    device = config_data["device"]
    assert device["manufacturer"] == "Wiener Netze"
    assert device["model"] == "Smart Meter"
    assert f"wnsm_{config.zp}" in device["identifiers"][0]
    
    print("✅ Home Assistant discovery configuration works correctly")


def test_discovery_all_configs():
    """Test getting all discovery configurations."""
    
    config = WNSMConfig(
        wnsm_username="test",
        wnsm_password="test",
        zp="AT0010000000000000001000004392265",
        mqtt_host="localhost"
    )
    
    discovery = HomeAssistantDiscovery(config)
    all_configs = discovery.get_all_discovery_configs()
    
    # Should have 3 sensors: energy, total, status
    assert len(all_configs) == 3
    
    # Check that all configs have required fields
    for config_item in all_configs:
        assert "topic" in config_item
        assert "config" in config_item
        assert config_item["topic"].startswith("homeassistant/sensor/")
    
    print("✅ All discovery configurations work correctly")


if __name__ == "__main__":
    print("Testing MQTT functionality...")
    
    test_mqtt_host_parsing()
    test_mqtt_auth_preparation()
    test_mqtt_publish_message()
    test_home_assistant_discovery()
    test_discovery_all_configs()
    
    print("\n🎉 All MQTT tests passed!")