import os
import sys
import json
import builtins
import pytest
from unittest import mock
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from wnsm_sync.config.loader import ConfigLoader
from wnsm_sync.core.sync import WNSMSync

@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Clear relevant environment variables before each test."""
    keys = [
        "WNSM_USERNAME", "WNSM_PASSWORD", "USE_EXTERNAL_MQTT", "HA_URL", "STAT_ID",
        "MQTT_HOST", "MQTT_PORT", "MQTT_TOPIC", "MQTT_USERNAME", "MQTT_PASSWORD",
        "HISTORY_DAYS", "RETRY_COUNT", "RETRY_DELAY", "UPDATE_INTERVAL", "SESSION_FILE", "WNSM_ZP"
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)

def test_load_config_from_env(monkeypatch):
    """Test loading configuration from environment variables."""
    monkeypatch.setenv("WNSM_USERNAME", "user1")
    monkeypatch.setenv("WNSM_PASSWORD", "pass1")
    monkeypatch.setenv("ZP", "AT0010000000000000001000004392265")
    monkeypatch.setenv("MQTT_HOST", "localhost")
    monkeypatch.setenv("MQTT_PORT", "1884")
    monkeypatch.setenv("HISTORY_DAYS", "2")
    monkeypatch.setenv("RETRY_COUNT", "5")
    monkeypatch.setenv("RETRY_DELAY", "7")
    monkeypatch.setenv("UPDATE_INTERVAL", "3600")

    loader = ConfigLoader()
    config = loader.load()
    
    assert config.wnsm_username == "user1"
    assert config.wnsm_password == "pass1"
    assert config.zp == "AT0010000000000000001000004392265"
    assert config.mqtt_host == "localhost"
    assert config.mqtt_port == 1884
    assert config.history_days == 2
    assert config.retry_count == 5
    assert config.retry_delay == 7
    assert config.update_interval == 3600

def test_sync_with_mock_data(monkeypatch):
    """Test the complete sync process with mock data."""
    # Set up environment for mock data
    monkeypatch.setenv("WNSM_USERNAME", "test_user")
    monkeypatch.setenv("WNSM_PASSWORD", "test_pass")
    monkeypatch.setenv("ZP", "AT0010000000000000001000004392265")
    monkeypatch.setenv("MQTT_HOST", "localhost")
    monkeypatch.setenv("USE_MOCK_DATA", "true")
    
    # Load config and create sync
    loader = ConfigLoader()
    config = loader.load()
    sync = WNSMSync(config)
    
    # Test that we can fetch mock data
    energy_data = sync.fetch_energy_data()
    assert energy_data is not None
    assert len(energy_data.readings) > 0
    assert energy_data.total_kwh > 0
    
    # Test that all readings have valid data
    for reading in energy_data.readings:
        assert reading.value_kwh > 0
        assert reading.quality == "mock"

def test_missing_required_config():
    """Test that missing required configuration raises ValueError."""
    with pytest.raises(ValueError, match="username"):
        from wnsm_sync.config.loader import WNSMConfig
        WNSMConfig(
            wnsm_username="",  # Empty username should fail
            wnsm_password="test_pass",
            zp="AT0010000000000000001000004392265",
            mqtt_host="localhost"
        )