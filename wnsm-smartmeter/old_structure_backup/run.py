#!/usr/bin/env python3
"""Entry point for the Wiener Netze Smart Meter Home Assistant Add-on."""
import os
import sys
import logging
import time
import json

# Set log level based on DEBUG environment variable
log_level = logging.DEBUG if os.environ.get("DEBUG", "").lower() in ("true", "1", "yes") else logging.INFO

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("wnsm-addon")

if log_level == logging.DEBUG:
    logger.debug("Debug logging enabled")

try:
    # Import required modules
    from wnsm_sync.sync_bewegungsdaten_to_ha import (
        fetch_bewegungsdaten,
        publish_mqtt_discovery,
        publish_mqtt_data
    )
    
    # Try importing vienna-smartmeter to verify it's installed
    import vienna_smartmeter
    import inspect
    
    try:
        logger.info(f"Using vienna-smartmeter version: {vienna_smartmeter.__version__}")
    except AttributeError:
        logger.info("Using vienna-smartmeter from GitHub (version info not available)")
    
    # Check if the Smartmeter class has the bewegungsdaten method
    if hasattr(vienna_smartmeter.Smartmeter, 'bewegungsdaten'):
        logger.info("vienna-smartmeter library has bewegungsdaten method")
    else:
        logger.warning("vienna-smartmeter library does not have bewegungsdaten method - will use fallback implementation")
    
    # Log available methods in debug mode
    if os.environ.get('DEBUG', '').lower() == 'true' or log_level == logging.DEBUG:
        try:
            methods = [m[0] for m in inspect.getmembers(vienna_smartmeter.Smartmeter, predicate=inspect.isfunction)]
            logger.debug(f"Available methods in Smartmeter class: {methods}")
        except Exception as e:
            logger.error(f"Error inspecting Smartmeter class: {e}")
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure vienna-smartmeter is installed. Run: pip install git+https://github.com/cretl/vienna-smartmeter.git@fix-login-add-pkce")
    sys.exit(1)

def load_config():
    """Load configuration from options.json or environment variables."""
    config = {}
    
    # First try to load from options.json (preferred method for Home Assistant addons)
    options_file = "/data/options.json"
    if os.path.exists(options_file):
        try:
            logger.info(f"Loading configuration from {options_file}")
            with open(options_file, 'r') as f:
                options = json.loads(f.read())
                logger.debug(f"Loaded options: {', '.join(options.keys())}")
                
                # Transfer all options to our config
                for key, value in options.items():
                    config[key] = value
                    
        except Exception as e:
            logger.error(f"Failed to load options.json: {e}")
    else:
        logger.warning(f"Options file {options_file} not found, falling back to environment variables")
    
    # Debug: Print all environment variables to help diagnose issues
    logger.debug("Environment variables:")
    for key, value in os.environ.items():
        logger.debug(f"  {key}: {value if 'PASSWORD' not in key else '****'}")
    
    # Fall back to environment variables for any missing values
    env_mappings = {
        "WNSM_USERNAME": ["WNSM_USERNAME", "USERNAME"],
        "WNSM_PASSWORD": ["WNSM_PASSWORD", "PASSWORD"],
        "ZP": ["WNSM_ZP", "ZP"],
        "MQTT_HOST": ["MQTT_HOST"],
        "MQTT_PORT": ["MQTT_PORT"],
        "MQTT_USERNAME": ["MQTT_USERNAME"],
        "MQTT_PASSWORD": ["MQTT_PASSWORD"],
        "MQTT_TOPIC": ["MQTT_TOPIC"],
        "UPDATE_INTERVAL": ["UPDATE_INTERVAL"],
        "DEBUG": ["DEBUG"],
        "USE_MOCK_DATA": ["WNSM_USE_MOCK_DATA", "USE_MOCK_DATA"]
    }
    
    # For each config key, try all possible environment variable names
    for config_key, env_vars in env_mappings.items():
        if config_key not in config or not config[config_key]:
            for env_var in env_vars:
                if env_var in os.environ and os.environ[env_var]:
                    value = os.environ[env_var]
                    # Convert numeric values
                    if config_key in ["MQTT_PORT", "UPDATE_INTERVAL"]:
                        try:
                            value = int(value)
                        except ValueError:
                            logger.warning(f"Could not convert {env_var}='{value}' to integer")
                    config[config_key] = value
                    logger.debug(f"Using environment variable {env_var} for {config_key}")
                    break
    
    # Set defaults for optional parameters
    defaults = {
        "MQTT_PORT": 1883,
        "MQTT_TOPIC": "smartmeter/energy/state",
        "UPDATE_INTERVAL": 3600,
        "USE_MOCK_DATA": False  # Default to using real API data
    }
    
    for key, default_value in defaults.items():
        if key not in config or config[key] is None:
            config[key] = default_value
            logger.debug(f"Using default value for {key}: {default_value}")
    
    # Debug: Print final config
    logger.debug("Final configuration:")
    for key, value in config.items():
        logger.debug(f"  {key}: {value if 'PASSWORD' not in key else '****'}")
    
    return config

def main():
    try:
        config = load_config()

        required_fields = ["WNSM_USERNAME", "WNSM_PASSWORD", "ZP", "MQTT_HOST"]
        missing_fields = [field for field in required_fields if not config.get(field)]

        if missing_fields:
            logger.error(f"Missing required configuration: {', '.join(missing_fields)}")
            logger.error("Please configure these values in the Home Assistant addon configuration")
            sys.exit(1)

        logger.info("Wiener Netze Smart Meter Add-on started")
        
        # Log whether we're using mock data
        if config.get("USE_MOCK_DATA"):
            logger.warning("MOCK DATA MODE ENABLED - Using simulated data instead of real API calls")

        while True:
            logger.info("Publishing MQTT discovery configuration")
            publish_mqtt_discovery(config)

            logger.info("Fetching Bewegungsdaten from Wiener Netze")
            statistics = fetch_bewegungsdaten(config)

            if statistics:
                # Check the format of the statistics
                if isinstance(statistics, dict):
                    if 'data' in statistics:
                        logger.info(f"Fetched {len(statistics['data'])} data points")
                    elif 'values' in statistics:
                        logger.info(f"Fetched {len(statistics['values'])} data points")
                    else:
                        logger.info(f"Fetched data in dictionary format with keys: {list(statistics.keys())}")
                elif isinstance(statistics, list):
                    logger.info(f"Fetched {len(statistics)} data points")
                else:
                    logger.info(f"Fetched data in unexpected format: {type(statistics)}")
                
                # The publish_mqtt_data function will handle the data format conversion
                publish_mqtt_data(statistics, config)
            else:
                logger.warning("No data fetched from Wiener Netze")

            logger.info(f"Sleeping for {config['UPDATE_INTERVAL']} seconds")
            time.sleep(config["UPDATE_INTERVAL"])

    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()