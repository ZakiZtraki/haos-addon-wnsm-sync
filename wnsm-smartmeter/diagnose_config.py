#!/usr/bin/env python3
"""
Diagnostic script to help troubleshoot configuration and secrets loading issues.
"""

import os
import json
import yaml
import sys

def check_options_file():
    """Check the add-on options.json file."""
    print("=== Checking options.json ===")
    
    options_file = "/data/options.json"
    if os.path.exists(options_file):
        try:
            with open(options_file, 'r') as f:
                options = json.load(f)
            
            print(f"✅ Found options.json with {len(options)} keys")
            print("Configuration:")
            for key, value in options.items():
                if 'PASSWORD' in key.upper():
                    print(f"  {key}: {'****' if value else '(empty)'}")
                else:
                    print(f"  {key}: {value}")
            
            use_secrets = options.get("USE_SECRETS", False)
            print(f"\nUSE_SECRETS mode: {use_secrets}")
            
            # Check for empty credential fields
            credential_fields = ["WNSM_USERNAME", "WNSM_PASSWORD", "ZP"]
            empty_fields = [field for field in credential_fields if not options.get(field)]
            if empty_fields:
                print(f"Empty credential fields: {empty_fields}")
            
            return options
            
        except Exception as e:
            print(f"❌ Error reading options.json: {e}")
            return None
    else:
        print(f"❌ options.json not found at {options_file}")
        return None

def check_secrets_file():
    """Check for secrets.yaml files."""
    print("\n=== Checking secrets.yaml ===")
    
    secrets_paths = [
        "/config/secrets.yaml",
        "/homeassistant/secrets.yaml", 
        "/data/secrets.yaml"
    ]
    
    for path in secrets_paths:
        print(f"Checking {path}...")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    secrets = yaml.safe_load(f) or {}
                
                print(f"✅ Found secrets.yaml at {path}")
                print(f"   Contains {len(secrets)} secrets")
                
                # Check for common secret names
                common_names = [
                    'wnsm_username', 'username', 
                    'wnsm_password', 'password',
                    'wnsm_zp', 'zp', 'wnsm_meter', 'meter'
                ]
                
                found_secrets = [name for name in common_names if name in secrets]
                if found_secrets:
                    print(f"   Found credential secrets: {found_secrets}")
                else:
                    print("   ⚠️  No credential secrets found with common names")
                
                print(f"   All secret keys: {list(secrets.keys())}")
                return secrets, path
                
            except Exception as e:
                print(f"❌ Error reading {path}: {e}")
        else:
            print(f"   Not found")
    
    print("❌ No secrets.yaml file found")
    return None, None

def check_environment():
    """Check environment variables."""
    print("\n=== Checking Environment Variables ===")
    
    env_vars = [
        'WNSM_USERNAME', 'USERNAME',
        'WNSM_PASSWORD', 'PASSWORD', 
        'WNSM_ZP', 'ZP'
    ]
    
    found_vars = []
    for var in env_vars:
        if var in os.environ:
            value = os.environ[var]
            if 'PASSWORD' in var:
                print(f"  {var}: ****")
            else:
                print(f"  {var}: {value}")
            found_vars.append(var)
    
    if found_vars:
        print(f"✅ Found {len(found_vars)} credential environment variables")
    else:
        print("❌ No credential environment variables found")

def simulate_config_loading():
    """Simulate the configuration loading process."""
    print("\n=== Simulating Configuration Loading ===")
    
    # Load options
    options = check_options_file()
    if not options:
        print("❌ Cannot proceed without options.json")
        return
    
    # Check secrets
    secrets, secrets_path = check_secrets_file()
    
    # Simulate the loading logic
    config = {}
    use_secrets = options.get("USE_SECRETS", False)
    
    # Map options to config
    key_mapping = {
        "WNSM_USERNAME": "USERNAME",
        "WNSM_PASSWORD": "PASSWORD", 
        "WNSM_ZP": "ZP",
        "ZP": "ZP",
        "MQTT_HOST": "MQTT_HOST"
    }
    
    for options_key, config_key in key_mapping.items():
        if options_key in options and options[options_key] is not None and options[options_key] != "":
            config[config_key] = options[options_key]
    
    print(f"After loading from options.json: {list(config.keys())}")
    
    # Check if secrets are needed
    missing_required = not all(key in config and config[key] for key in ["USERNAME", "PASSWORD", "ZP"])
    
    print(f"USE_SECRETS: {use_secrets}")
    print(f"Missing required: {missing_required}")
    
    if (use_secrets or missing_required) and secrets:
        print("Applying secrets...")
        
        secret_mappings = {
            "USERNAME": ["wnsm_username", "username"],
            "PASSWORD": ["wnsm_password", "password"],
            "ZP": ["wnsm_zp", "zp", "wnsm_meter", "meter"]
        }
        
        if use_secrets:
            # USE_SECRETS=true: Override all mapped values
            for config_key, secret_names in secret_mappings.items():
                for secret_name in secret_names:
                    if secret_name in secrets:
                        config[config_key] = secrets[secret_name]
                        print(f"  Applied secret '{secret_name}' to {config_key}")
                        break
        else:
            # Automatic fallback: Only fill missing
            for config_key in ["USERNAME", "PASSWORD", "ZP"]:
                if config_key not in config or not config[config_key]:
                    secret_names = secret_mappings.get(config_key, [])
                    for secret_name in secret_names:
                        if secret_name in secrets:
                            config[config_key] = secrets[secret_name]
                            print(f"  Filled missing {config_key} with secret '{secret_name}'")
                            break
    
    # Final check
    required_keys = ["USERNAME", "PASSWORD", "ZP"]
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    print(f"\nFinal configuration keys: {list(config.keys())}")
    
    if missing_keys:
        print(f"❌ Still missing: {missing_keys}")
        return False
    else:
        print("✅ All required credentials found!")
        return True

def main():
    """Main diagnostic function."""
    print("🔍 WNSM Add-on Configuration Diagnostics")
    print("=" * 50)
    
    # Check if we're running in the add-on environment
    if not os.path.exists("/data"):
        print("⚠️  Not running in Home Assistant add-on environment")
        print("   This script is designed to run inside the add-on container")
        return
    
    success = simulate_config_loading()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Configuration should work correctly!")
    else:
        print("❌ Configuration issues detected")
        print("\n💡 Troubleshooting suggestions:")
        print("1. Make sure USE_SECRETS is enabled in add-on config")
        print("2. Check that secrets.yaml exists at /config/secrets.yaml")
        print("3. Verify secret names match expected patterns:")
        print("   - wnsm_username or username")
        print("   - wnsm_password or password") 
        print("   - wnsm_zp, zp, wnsm_meter, or meter")
        print("4. Restart the add-on after making changes")

if __name__ == "__main__":
    main()