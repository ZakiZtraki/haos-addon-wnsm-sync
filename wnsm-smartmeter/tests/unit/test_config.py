#!/usr/bin/env python3
"""Tests for configuration loading and secrets management."""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from wnsm_sync.config.loader import ConfigLoader, WNSMConfig
from wnsm_sync.config.secrets import SecretsManager


def test_config_validation():
    """Test configuration validation."""
    
    # Test valid config
    config = WNSMConfig(
        wnsm_username="test_user",
        wnsm_password="test_pass",
        zp="AT0010000000000000001000004392265",
        mqtt_host="localhost"
    )
    
    assert config.wnsm_username == "test_user"
    assert config.mqtt_port == 1883  # Default value
    assert config.update_interval == 3600  # Default value
    
    print("✅ Valid configuration works correctly")


def test_config_validation_errors():
    """Test configuration validation errors."""
    
    try:
        # Missing required field
        WNSMConfig(
            wnsm_username="",  # Empty username
            wnsm_password="test_pass",
            zp="AT0010000000000000001000004392265",
            mqtt_host="localhost"
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "username" in str(e).lower()
        print("✅ Empty username validation works")
    
    try:
        # Invalid port
        WNSMConfig(
            wnsm_username="test_user",
            wnsm_password="test_pass",
            zp="AT0010000000000000001000004392265",
            mqtt_host="localhost",
            mqtt_port=0  # Invalid port
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "port" in str(e).lower()
        print("✅ Invalid port validation works")


def test_secrets_manager():
    """Test secrets manager functionality."""
    
    # Create temporary secrets file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
wnsm_username: secret_user
wnsm_password: secret_pass
mqtt_password: mqtt_secret
""")
        secrets_file = f.name
    
    try:
        # Test secrets loading
        secrets_manager = SecretsManager([secrets_file])
        
        assert secrets_manager.has_secrets()
        assert secrets_manager.get_secret("wnsm_username") == "secret_user"
        
        # Test secret resolution
        resolved = secrets_manager.resolve_value("!secret wnsm_username")
        assert resolved == "secret_user"
        
        # Test non-secret value
        resolved = secrets_manager.resolve_value("plain_value")
        assert resolved == "plain_value"
        
        print("✅ Secrets manager works correctly")
        
    finally:
        os.unlink(secrets_file)


def test_config_loader_with_options():
    """Test config loader with options.json file."""
    
    # Create temporary options file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        options = {
            "WNSM_USERNAME": "test_user",
            "WNSM_PASSWORD": "test_pass", 
            "ZP": "AT0010000000000000001000004392265",
            "MQTT_HOST": "localhost",
            "MQTT_PORT": 1883,
            "DEBUG": True
        }
        json.dump(options, f)
        options_file = f.name
    
    try:
        # Mock the options file path
        original_options_file = ConfigLoader.OPTIONS_FILE
        ConfigLoader.OPTIONS_FILE = options_file
        
        loader = ConfigLoader()
        config = loader.load()
        
        assert config.wnsm_username == "test_user"
        assert config.mqtt_host == "localhost"
        assert config.debug == True
        
        print("✅ Config loader with options.json works correctly")
        
    finally:
        ConfigLoader.OPTIONS_FILE = original_options_file
        os.unlink(options_file)


if __name__ == "__main__":
    print("Testing configuration management...")
    
    test_config_validation()
    test_config_validation_errors()
    test_secrets_manager()
    test_config_loader_with_options()
    
    print("\n🎉 All configuration tests passed!")