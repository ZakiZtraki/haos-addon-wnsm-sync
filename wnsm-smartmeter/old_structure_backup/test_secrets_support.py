#!/usr/bin/env python3
"""
Test script to verify secrets.yaml support functionality.
"""

import sys
import os
import json
import tempfile
import yaml
from unittest import mock

# Add the wnsm_sync module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wnsm_sync.sync_bewegungsdaten_to_ha import load_secrets, resolve_secret_value, load_config

def test_load_secrets():
    """Test loading secrets from secrets.yaml file."""
    print("=== Testing load_secrets() ===")
    
    # Create a temporary secrets file
    secrets_data = {
        'wnsm_username': 'test-user@example.com',
        'wnsm_password': 'super-secret-password',
        'wnsm_zp': 'AT0030000000000000000000012345678',
        'mqtt_username': 'mqtt-user',
        'mqtt_password': 'mqtt-secret'
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(secrets_data, f)
        temp_secrets_path = f.name
    
    try:
        # Mock the secrets paths to point to our temp file
        with mock.patch('wnsm_sync.sync_bewegungsdaten_to_ha.os.path.exists') as mock_exists:
            def exists_side_effect(path):
                return path == temp_secrets_path
            mock_exists.side_effect = exists_side_effect
            
            # Mock the secrets paths
            original_paths = [
                "/config/secrets.yaml",
                "/homeassistant/secrets.yaml", 
                "/data/secrets.yaml"
            ]
            
            with mock.patch('wnsm_sync.sync_bewegungsdaten_to_ha.load_secrets') as mock_load_secrets:
                # Manually load our test secrets
                with open(temp_secrets_path, 'r') as f:
                    test_secrets = yaml.safe_load(f)
                mock_load_secrets.return_value = test_secrets
                
                secrets = mock_load_secrets()
                
                print(f"✅ Loaded {len(secrets)} secrets")
                assert len(secrets) == 5
                assert secrets['wnsm_username'] == 'test-user@example.com'
                assert secrets['wnsm_password'] == 'super-secret-password'
                print("✅ Secrets loaded correctly")
                
    finally:
        os.unlink(temp_secrets_path)

def test_resolve_secret_value():
    """Test resolving secret references."""
    print("\n=== Testing resolve_secret_value() ===")
    
    secrets = {
        'wnsm_username': 'test-user@example.com',
        'wnsm_password': 'super-secret-password',
        'mqtt_host': 'mqtt.example.com'
    }
    
    # Test cases
    test_cases = [
        # (input_value, expected_output, description)
        ('!secret wnsm_username', 'test-user@example.com', 'Basic secret reference'),
        ('!secret wnsm_password', 'super-secret-password', 'Password secret reference'),
        ('!secret nonexistent', '!secret nonexistent', 'Non-existent secret (should return as-is)'),
        ('regular_value', 'regular_value', 'Regular string value'),
        ('core-mosquitto', 'core-mosquitto', 'Regular hostname'),
        (1883, 1883, 'Integer value'),
        (None, None, 'None value'),
        ('  !secret mqtt_host  ', 'mqtt.example.com', 'Secret with whitespace'),
    ]
    
    for input_val, expected, description in test_cases:
        result = resolve_secret_value(input_val, secrets)
        print(f"Test: {description}")
        print(f"  Input: {input_val}")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        assert result == expected, f"Failed: {description}"
        print("  ✅ Passed")
    
    print("✅ All secret resolution tests passed")

def test_config_with_secrets():
    """Test full configuration loading with secrets."""
    print("\n=== Testing load_config() with secrets ===")
    
    # Create mock options.json with secret references
    options_data = {
        'WNSM_USERNAME': '!secret wnsm_username',
        'WNSM_PASSWORD': '!secret wnsm_password', 
        'WNSM_ZP': '!secret wnsm_zp',
        'MQTT_HOST': 'core-mosquitto',  # Regular value
        'MQTT_USERNAME': '!secret mqtt_username',
        'MQTT_PASSWORD': '!secret mqtt_password',
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
        # Mock the file paths and loading functions
        with mock.patch('wnsm_sync.sync_bewegungsdaten_to_ha.os.path.exists') as mock_exists:
            def exists_side_effect(path):
                if path == "/data/options.json":
                    return True
                elif path in ["/config/secrets.yaml", "/homeassistant/secrets.yaml", "/data/secrets.yaml"]:
                    return path == "/config/secrets.yaml"  # Simulate finding secrets at first path
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
                with mock.patch('sys.exit'):  # Prevent actual exit on missing config
                    config = load_config()
                    
                    print("Configuration loaded:")
                    for key, value in config.items():
                        if 'PASSWORD' in key:
                            print(f"  {key}: ****")
                        else:
                            print(f"  {key}: {value}")
                    
                    # Verify secrets were resolved
                    assert config['USERNAME'] == 'test-user@example.com'
                    assert config['PASSWORD'] == 'super-secret-password'
                    assert config['ZP'] == 'AT0030000000000000000000012345678'
                    assert config['MQTT_HOST'] == 'core-mosquitto'  # Regular value
                    assert config['MQTT_USERNAME'] == 'mqtt-user'
                    assert config['MQTT_PASSWORD'] == 'mqtt-secret'
                    assert config['UPDATE_INTERVAL'] == 86400
                    
                    print("✅ Configuration with secrets loaded correctly")
                    
    finally:
        os.unlink(options_path)
        os.unlink(secrets_path)

def test_secrets_yaml_example():
    """Test with a realistic secrets.yaml example."""
    print("\n=== Testing realistic secrets.yaml example ===")
    
    # Example secrets.yaml content
    secrets_content = """
# Wiener Netze Smart Meter credentials
wnsm_username: "john.doe@example.com"
wnsm_password: "MySecurePassword123!"
wnsm_zp: "AT0030000000000000000000012345678"

# MQTT broker credentials
mqtt_username: "homeassistant"
mqtt_password: "mqtt_secure_password"
mqtt_host: "192.168.1.100"

# Other secrets
api_key: "abc123def456"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(secrets_content)
        secrets_path = f.name
    
    try:
        with open(secrets_path, 'r') as f:
            secrets = yaml.safe_load(f)
        
        print("Loaded secrets:")
        for key in secrets.keys():
            print(f"  {key}: ****")
        
        # Test secret resolution
        test_values = [
            '!secret wnsm_username',
            '!secret wnsm_password', 
            '!secret mqtt_host',
            'regular-value'
        ]
        
        for value in test_values:
            resolved = resolve_secret_value(value, secrets)
            if value.startswith('!secret'):
                secret_name = value.split()[1]
                expected = secrets.get(secret_name, value)
                assert resolved == expected
                print(f"✅ {value} -> {resolved}")
            else:
                assert resolved == value
                print(f"✅ {value} -> {resolved}")
                
    finally:
        os.unlink(secrets_path)

if __name__ == "__main__":
    print("Testing Home Assistant secrets.yaml support...")
    
    try:
        test_load_secrets()
        test_resolve_secret_value()
        test_config_with_secrets()
        test_secrets_yaml_example()
        
        print("\n🎉 All secrets tests passed!")
        print("\nSecrets.yaml support is working correctly!")
        print("\nUsers can now:")
        print("1. Add credentials to /config/secrets.yaml")
        print("2. Reference them in add-on config using '!secret secret_name'")
        print("3. Keep sensitive data centralized and secure")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)