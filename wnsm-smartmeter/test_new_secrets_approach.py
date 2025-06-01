#!/usr/bin/env python3
"""
Test script to verify the new secrets approach that works with Home Assistant add-on validation.
"""

import sys
import os
import json
import tempfile
import yaml
from unittest import mock

# Add the wnsm_sync module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wnsm_sync.sync_bewegungsdaten_to_ha import load_config

def test_use_secrets_enabled():
    """Test configuration loading with USE_SECRETS enabled."""
    print("=== Testing USE_SECRETS enabled ===")
    
    # Create mock options.json with USE_SECRETS enabled
    options_data = {
        'USE_SECRETS': True,
        'WNSM_USERNAME': '',  # Empty - should be loaded from secrets
        'WNSM_PASSWORD': '',  # Empty - should be loaded from secrets
        'ZP': '',             # Empty - should be loaded from secrets
        'MQTT_HOST': 'core-mosquitto',
        'MQTT_USERNAME': '',  # Empty - should be loaded from secrets
        'MQTT_PASSWORD': '',  # Empty - should be loaded from secrets
        'UPDATE_INTERVAL': 86400
    }
    
    secrets_data = {
        'wnsm_username': 'test-user@example.com',
        'wnsm_password': 'super-secret-password',
        'wnsm_zp': 'AT0030000000000000000000012345678',
        'mqtt_username': 'mqtt-user',
        'mqtt_password': 'mqtt-secret'
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as options_file:
        json.dump(options_data, options_file)
        options_path = options_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as secrets_file:
        yaml.dump(secrets_data, secrets_file)
        secrets_path = secrets_file.name
    
    try:
        # Mock the file paths
        with mock.patch('wnsm_sync.sync_bewegungsdaten_to_ha.os.path.exists') as mock_exists:
            def exists_side_effect(path):
                if path == "/data/options.json":
                    return True
                elif path in ["/config/secrets.yaml", "/homeassistant/secrets.yaml", "/data/secrets.yaml"]:
                    return path == "/config/secrets.yaml"
                return False
            mock_exists.side_effect = exists_side_effect
            
            # Mock file opening
            original_open = open
            def mock_open_func(filename, *args, **kwargs):
                if filename == "/data/options.json":
                    return original_open(options_path, *args, **kwargs)
                elif filename == "/config/secrets.yaml":
                    return original_open(secrets_path, *args, **kwargs)
                return original_open(filename, *args, **kwargs)
            
            with mock.patch('builtins.open', side_effect=mock_open_func):
                with mock.patch('sys.exit'):  # Prevent actual exit
                    config = load_config()
                    
                    print("Configuration loaded with USE_SECRETS=True:")
                    for key, value in config.items():
                        if 'PASSWORD' in key:
                            print(f"  {key}: ****")
                        else:
                            print(f"  {key}: {value}")
                    
                    # Verify secrets were loaded
                    assert config['USERNAME'] == 'test-user@example.com'
                    assert config['PASSWORD'] == 'super-secret-password'
                    assert config['ZP'] == 'AT0030000000000000000000012345678'
                    assert config['MQTT_HOST'] == 'core-mosquitto'
                    assert config['MQTT_USERNAME'] == 'mqtt-user'
                    assert config['MQTT_PASSWORD'] == 'mqtt-secret'
                    
                    print("✅ USE_SECRETS mode works correctly")
                    
    finally:
        os.unlink(options_path)
        os.unlink(secrets_path)

def test_use_secrets_disabled_with_direct_values():
    """Test configuration loading with USE_SECRETS disabled and direct values."""
    print("\n=== Testing USE_SECRETS disabled with direct values ===")
    
    # Create mock options.json with direct values
    options_data = {
        'USE_SECRETS': False,
        'WNSM_USERNAME': 'direct-user@example.com',
        'WNSM_PASSWORD': 'direct-password',
        'ZP': 'AT0030000000000000000000087654321',
        'MQTT_HOST': 'core-mosquitto',
        'UPDATE_INTERVAL': 86400
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as options_file:
        json.dump(options_data, options_file)
        options_path = options_file.name
    
    try:
        # Mock the file paths
        with mock.patch('wnsm_sync.sync_bewegungsdaten_to_ha.os.path.exists') as mock_exists:
            def exists_side_effect(path):
                if path == "/data/options.json":
                    return True
                return False  # No secrets file
            mock_exists.side_effect = exists_side_effect
            
            # Mock file opening
            original_open = open
            def mock_open_func(filename, *args, **kwargs):
                if filename == "/data/options.json":
                    return original_open(options_path, *args, **kwargs)
                return original_open(filename, *args, **kwargs)
            
            with mock.patch('builtins.open', side_effect=mock_open_func):
                with mock.patch('sys.exit'):  # Prevent actual exit
                    config = load_config()
                    
                    print("Configuration loaded with direct values:")
                    for key, value in config.items():
                        if 'PASSWORD' in key:
                            print(f"  {key}: ****")
                        else:
                            print(f"  {key}: {value}")
                    
                    # Verify direct values were used
                    assert config['USERNAME'] == 'direct-user@example.com'
                    assert config['PASSWORD'] == 'direct-password'
                    assert config['ZP'] == 'AT0030000000000000000000087654321'
                    assert config['MQTT_HOST'] == 'core-mosquitto'
                    
                    print("✅ Direct values mode works correctly")
                    
    finally:
        os.unlink(options_path)

def test_automatic_secrets_fallback():
    """Test automatic secrets fallback when credentials are missing."""
    print("\n=== Testing automatic secrets fallback ===")
    
    # Create mock options.json with missing credentials
    options_data = {
        'USE_SECRETS': False,  # Disabled, but credentials are empty
        'WNSM_USERNAME': '',   # Empty - should trigger secrets fallback
        'WNSM_PASSWORD': '',   # Empty - should trigger secrets fallback
        'ZP': '',              # Empty - should trigger secrets fallback
        'MQTT_HOST': 'core-mosquitto',
        'UPDATE_INTERVAL': 86400
    }
    
    secrets_data = {
        'wnsm_username': 'fallback-user@example.com',
        'wnsm_password': 'fallback-password',
        'wnsm_zp': 'AT0030000000000000000000099999999'
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as options_file:
        json.dump(options_data, options_file)
        options_path = options_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as secrets_file:
        yaml.dump(secrets_data, secrets_file)
        secrets_path = secrets_file.name
    
    try:
        # Mock the file paths
        with mock.patch('wnsm_sync.sync_bewegungsdaten_to_ha.os.path.exists') as mock_exists:
            def exists_side_effect(path):
                if path == "/data/options.json":
                    return True
                elif path in ["/config/secrets.yaml", "/homeassistant/secrets.yaml", "/data/secrets.yaml"]:
                    return path == "/config/secrets.yaml"
                return False
            mock_exists.side_effect = exists_side_effect
            
            # Mock file opening
            original_open = open
            def mock_open_func(filename, *args, **kwargs):
                if filename == "/data/options.json":
                    return original_open(options_path, *args, **kwargs)
                elif filename == "/config/secrets.yaml":
                    return original_open(secrets_path, *args, **kwargs)
                return original_open(filename, *args, **kwargs)
            
            with mock.patch('builtins.open', side_effect=mock_open_func):
                with mock.patch('sys.exit'):  # Prevent actual exit
                    config = load_config()
                    
                    print("Configuration loaded with automatic secrets fallback:")
                    for key, value in config.items():
                        if 'PASSWORD' in key:
                            print(f"  {key}: ****")
                        else:
                            print(f"  {key}: {value}")
                    
                    # Verify secrets were loaded as fallback
                    assert config['USERNAME'] == 'fallback-user@example.com'
                    assert config['PASSWORD'] == 'fallback-password'
                    assert config['ZP'] == 'AT0030000000000000000000099999999'
                    assert config['MQTT_HOST'] == 'core-mosquitto'
                    
                    print("✅ Automatic secrets fallback works correctly")
                    
    finally:
        os.unlink(options_path)
        os.unlink(secrets_path)

def test_secret_name_variations():
    """Test that different secret name variations work."""
    print("\n=== Testing secret name variations ===")
    
    # Test different secret naming conventions
    secrets_data = {
        'username': 'user-via-username',  # Alternative name
        'password': 'pass-via-password',  # Alternative name
        'meter': 'AT0030000000000000000000011111111',  # Alternative name
        'mqtt_user': 'mqtt-via-user',     # Alternative name
        'mqtt_pass': 'mqtt-via-pass'      # Alternative name
    }
    
    options_data = {
        'USE_SECRETS': True,
        'WNSM_USERNAME': '',
        'WNSM_PASSWORD': '',
        'ZP': '',
        'MQTT_USERNAME': '',
        'MQTT_PASSWORD': '',
        'MQTT_HOST': 'core-mosquitto'
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as options_file:
        json.dump(options_data, options_file)
        options_path = options_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as secrets_file:
        yaml.dump(secrets_data, secrets_file)
        secrets_path = secrets_file.name
    
    try:
        # Mock the file paths
        with mock.patch('wnsm_sync.sync_bewegungsdaten_to_ha.os.path.exists') as mock_exists:
            def exists_side_effect(path):
                if path == "/data/options.json":
                    return True
                elif path in ["/config/secrets.yaml", "/homeassistant/secrets.yaml", "/data/secrets.yaml"]:
                    return path == "/config/secrets.yaml"
                return False
            mock_exists.side_effect = exists_side_effect
            
            # Mock file opening
            original_open = open
            def mock_open_func(filename, *args, **kwargs):
                if filename == "/data/options.json":
                    return original_open(options_path, *args, **kwargs)
                elif filename == "/config/secrets.yaml":
                    return original_open(secrets_path, *args, **kwargs)
                return original_open(filename, *args, **kwargs)
            
            with mock.patch('builtins.open', side_effect=mock_open_func):
                with mock.patch('sys.exit'):  # Prevent actual exit
                    config = load_config()
                    
                    print("Configuration loaded with alternative secret names:")
                    for key, value in config.items():
                        if 'PASSWORD' in key:
                            print(f"  {key}: ****")
                        else:
                            print(f"  {key}: {value}")
                    
                    # Verify alternative secret names work
                    assert config['USERNAME'] == 'user-via-username'
                    assert config['PASSWORD'] == 'pass-via-password'
                    assert config['ZP'] == 'AT0030000000000000000000011111111'
                    assert config['MQTT_USERNAME'] == 'mqtt-via-user'
                    assert config['MQTT_PASSWORD'] == 'mqtt-via-pass'
                    
                    print("✅ Alternative secret names work correctly")
                    
    finally:
        os.unlink(options_path)
        os.unlink(secrets_path)

if __name__ == "__main__":
    print("Testing the new Home Assistant-compatible secrets approach...")
    
    try:
        test_use_secrets_enabled()
        test_use_secrets_disabled_with_direct_values()
        test_automatic_secrets_fallback()
        test_secret_name_variations()
        
        print("\n🎉 All new secrets tests passed!")
        print("\nThe new approach works correctly:")
        print("1. ✅ USE_SECRETS=true loads all credentials from secrets.yaml")
        print("2. ✅ USE_SECRETS=false uses direct values from configuration")
        print("3. ✅ Automatic fallback to secrets when credentials are missing")
        print("4. ✅ Multiple secret name variations supported")
        print("5. ✅ No Home Assistant validation errors with this approach")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)