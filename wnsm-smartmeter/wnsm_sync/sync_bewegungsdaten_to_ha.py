#!/usr/bin/env python3
"""
Wiener Netze Smart Meter Sync Add-on for Home Assistant
Fetches 15-minute smart meter data and pushes to Home Assistant statistics.
"""
import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta, date
from decimal import Decimal
import paho.mqtt.publish as publish
import requests
from pathlib import Path

# Set log level based on DEBUG environment variable
log_level = logging.DEBUG if os.environ.get("DEBUG", "").lower() in ("true", "1", "yes") else logging.INFO

# Configure logging
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("wnsm_smartmeter")

if log_level == logging.DEBUG:
    logger.debug("Debug logging enabled")

# === CONFIGURATION ===
# Configuration from options.json with fallbacks to environment variables
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
                
                # Map options.json keys to our config keys
                key_mapping = {
                    "WNSM_USERNAME": "USERNAME",
                    "WNSM_PASSWORD": "PASSWORD",
                    "WNSM_ZP": "ZP",
                    "MQTT_HOST": "MQTT_HOST",
                    "MQTT_PORT": "MQTT_PORT",
                    "MQTT_USERNAME": "MQTT_USERNAME",
                    "MQTT_PASSWORD": "MQTT_PASSWORD",
                    "MQTT_TOPIC": "MQTT_TOPIC",
                    "UPDATE_INTERVAL": "UPDATE_INTERVAL",
                    "HISTORY_DAYS": "HISTORY_DAYS",
                    "RETRY_COUNT": "RETRY_COUNT",
                    "RETRY_DELAY": "RETRY_DELAY",
                    "HA_URL": "HA_URL",
                    "STAT_ID": "STATISTIC_ID",
                    "DEBUG": "DEBUG"
                }
                
                # Transfer all options to our config using the mapping
                for options_key, config_key in key_mapping.items():
                    if options_key in options and options[options_key] is not None:
                        config[config_key] = options[options_key]
                        logger.debug(f"Using {options_key} from options.json for {config_key}")
                
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
        "USERNAME": ["WNSM_USERNAME", "USERNAME"],
        "PASSWORD": ["WNSM_PASSWORD", "PASSWORD"],
        "ZP": ["WNSM_ZP", "ZP"],
        "USE_EXTERNAL_MQTT": ["USE_EXTERNAL_MQTT"],
        "HA_URL": ["HA_URL"],
        "STATISTIC_ID": ["STAT_ID", "STATISTIC_ID"],
        "MQTT_HOST": ["MQTT_HOST"],
        "MQTT_PORT": ["MQTT_PORT"],
        "MQTT_TOPIC": ["MQTT_TOPIC"],
        "MQTT_USERNAME": ["MQTT_USERNAME"],
        "MQTT_PASSWORD": ["MQTT_PASSWORD"],
        "HISTORY_DAYS": ["HISTORY_DAYS"],
        "RETRY_COUNT": ["RETRY_COUNT"],
        "RETRY_DELAY": ["RETRY_DELAY"],
        "UPDATE_INTERVAL": ["UPDATE_INTERVAL"],
        "SESSION_FILE": ["SESSION_FILE"]
    }
    
    # For each config key, try all possible environment variable names
    for config_key, env_vars in env_mappings.items():
        if config_key not in config or config[config_key] is None:
            for env_var in env_vars:
                if env_var in os.environ and os.environ[env_var]:
                    value = os.environ[env_var]
                    # Convert numeric values
                    if config_key in ["MQTT_PORT", "UPDATE_INTERVAL", "HISTORY_DAYS", "RETRY_COUNT", "RETRY_DELAY"]:
                        try:
                            value = int(value)
                        except ValueError:
                            logger.warning(f"Could not convert {env_var}='{value}' to integer")
                    config[config_key] = value
                    logger.debug(f"Using environment variable {env_var} for {config_key}")
                    break
    
    # Set defaults for optional parameters
    defaults = {
        "HA_URL": "http://homeassistant:8123",
        "STATISTIC_ID": "sensor.wiener_netze_energy",
        "MQTT_HOST": "core-mosquitto",
        "MQTT_PORT": 1883,
        "MQTT_TOPIC": "smartmeter/energy/state",
        "HISTORY_DAYS": 1,
        "RETRY_COUNT": 3,
        "RETRY_DELAY": 5,
        "UPDATE_INTERVAL": 86400,
        "SESSION_FILE": "/data/wnsm_session.json"
    }
    
    for key, default_value in defaults.items():
        if key not in config or config[key] is None:
            config[key] = default_value
            logger.debug(f"Using default value for {key}: {default_value}")
    
    # Debug: Print final config
    logger.debug("Final configuration:")
    for key, value in config.items():
        logger.debug(f"  {key}: {value if 'PASSWORD' not in key else '****'}")
    
    # Ensure we have the critical values
    required_keys = ["USERNAME", "PASSWORD", "ZP"]
    missing_keys = [key for key in required_keys if not config.get(key)]
    if missing_keys:
        logger.error(f"Missing required configuration: {', '.join(missing_keys)}")
        sys.exit(1)
        
    return config

def with_retry(func, config, *args, **kwargs):
    """Execute function with retry logic."""
    for attempt in range(1, config["RETRY_COUNT"] + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < config["RETRY_COUNT"]:
                delay = config["RETRY_DELAY"] * attempt  # Exponential backoff
                logger.warning(f"Attempt {attempt} failed: {str(e)}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"All {config['RETRY_COUNT']} attempts failed: {str(e)}")
                raise

def save_session(client, config):
    """Save session data for future use."""
    try:
        session_data = client.export_session()
        session_path = Path(config["SESSION_FILE"])
        
        # Ensure directory exists
        session_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(session_path, 'w') as f:
            json.dump(session_data, f)
        logger.info(f"Session saved to {session_path}")
    except Exception as e:
        logger.error(f"Failed to save session: {e}")

def load_session(client, config):
    """Try to load a previous session."""
    try:
        session_path = Path(config["SESSION_FILE"])
        if session_path.exists():
            with open(session_path, 'r') as f:
                session_data = json.load(f)
            client.restore_session(session_data)
            logger.info("Previous session restored")
            return True
    except Exception as e:
        logger.error(f"Failed to load session: {e}")
    return False

def parse_mqtt_host(mqtt_host):
    """Parse MQTT host string to extract protocol, hostname and port."""
    if not mqtt_host:
        return "localhost", 1883
        
    # If it's a URL format (mqtt://host:port)
    if "://" in mqtt_host:
        parts = mqtt_host.split("://")
        # protocol = parts[0]  # mqtt or mqtts
        host_port = parts[1]
        
        if ":" in host_port:
            host, port = host_port.split(":")
            return host, int(port)
        return host_port, 1883
    
    # If it's just a hostname or hostname:port
    if ":" in mqtt_host:
        host, port = mqtt_host.split(":")
        return host, int(port)
    
    return mqtt_host, 1883

# Function moved to a more comprehensive implementation below

def publish_mqtt_discovery(config):
    """Publish MQTT discovery configuration for Home Assistant."""
    try:
        device_id = config["ZP"].lower().replace("0", "")
        discovery_topic = f"homeassistant/sensor/wnsm_sync_{device_id}/config"
        discovery_payload = {
            "name": "WNSM 15min Energy",  # Clear name indicating 15-minute intervals
            "state_topic": config["MQTT_TOPIC"],
            "unit_of_measurement": "kWh",
            "device_class": "energy",
            "state_class": "measurement",  # Changed to measurement for delta values
            "unique_id": f"wnsm_sync_energy_sensor_{device_id}",
            "value_template": "{{ value_json.delta }}",  # Changed to use delta field
            "json_attributes_topic": config["MQTT_TOPIC"],
            "json_attributes_template": "{{ {'timestamp': value_json.timestamp} | tojson }}",
            "device": {
                "identifiers": [f"wnsm_sync_{device_id}"],
                "name": "Wiener Netze Smart Meter",  # This is the device name
                "manufacturer": "Wiener Netze",
                "model": "Smart Meter"
            }
        }
        
        publish_mqtt_message(discovery_topic, discovery_payload, config)
        logger.info("MQTT discovery configuration published")
    except Exception as e:
        logger.error(f"Failed to publish MQTT discovery: {e}")


def publish_mqtt_message(topic, payload, config):
    """Publish a message to MQTT with appropriate configuration."""
    try:
        # Always use direct MQTT connection
        import paho.mqtt.publish as publish

        # Extract host and port
        mqtt_host = config.get("MQTT_HOST", "localhost")
        mqtt_port = int(config.get("MQTT_PORT", 1883))

        # Prepare auth if credentials provided
        auth = None
        if config.get("MQTT_USERNAME") or config.get("MQTT_PASSWORD"):
            auth = {
                "username": config.get("MQTT_USERNAME", ""),
                "password": config.get("MQTT_PASSWORD", "")
            }

        publish.single(
            topic=topic,
            payload=json.dumps(payload),
            hostname=mqtt_host,
            port=mqtt_port,
            auth=auth,
            retain=True
        )
        return True
    except Exception as e:

        logger.error(f"Failed to publish to {topic}: {e}", exc_info=True)
        return False

def publish_mqtt_data(statistics, config):
    """Publish energy data to MQTT as individual 15-minute deltas."""
    if not statistics:
        logger.warning("No statistics to publish")
        return

    logger.info(f"Publishing {len(statistics)} 15-minute intervals to MQTT")

    # Sort statistics by timestamp to ensure proper ordering
    statistics.sort(key=lambda x: x.get('start', ''))
    
    # Publish each 15-minute interval as a separate MQTT message
    total_published = 0
    for entry in statistics:
        if not isinstance(entry, dict):
            logger.warning(f"Skipping invalid data point (not a dictionary): {entry}")
            continue
            
        if 'start' not in entry or 'delta' not in entry:
            logger.warning(f"Skipping data point with missing fields: {entry}")
            continue
        
        try:
            # Create the MQTT payload with the 15-minute delta value
            payload = {
                "delta": entry["delta"],  # 15-minute consumption in kWh
                "timestamp": entry["timestamp"]
            }
            
            # Publish to the main MQTT topic
            # Home Assistant will receive each 15-minute interval separately
            publish_mqtt_message(config["MQTT_TOPIC"], payload, config)
            total_published += 1
            
            logger.debug(f"Published 15-min interval: {entry['timestamp']} = {entry['delta']} kWh")
            
        except Exception as e:
            logger.warning(f"Error publishing entry {entry}: {e}")
            continue
    
    logger.info(f"✅ Published {total_published} 15-minute intervals to MQTT topic: {config['MQTT_TOPIC']}")
    
    # Log summary statistics
    if statistics:
        total_consumption = sum(s.get('delta', 0) for s in statistics)
        logger.info(f"Total consumption for period: {total_consumption:.3f} kWh across {len(statistics)} intervals")

def main():
    """Main function to run the sync process."""
    logger.info("==== Wiener Netze Smart Meter Sync starting ====")
    
    # Load configuration
    config = load_config()
    logger.info(f"Configuration loaded, using username: {config['USERNAME']}")
    
    # Import here to avoid early import errors
    try:
        from api.client import Smartmeter
        from api import constants as const
    except ImportError as e:
        logger.critical(f"Failed to import required modules: {e}")
        sys.exit(1)
    # Initialize Smartmeter client
    client = Smartmeter(config["USERNAME"], config["PASSWORD"])
    
    # Try to restore session first
    session_loaded = load_session(client, config)
    
    # Login if needed
    try:
        if not session_loaded or not client.is_logged_in():
            logger.info("Logging in to Wiener Netze...")
            with_retry(client.login, config)
            save_session(client, config)
        else:
            logger.info("Using existing session")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        sys.exit(1)
    
    # Calculate date range based on configuration
    end_date = date.today() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=config["HISTORY_DAYS"] - 1)
    
    logger.info(f"Fetching data from {start_date} to {end_date}")
    
    # Fetch bewegungsdaten with retry
    try:
        bewegungsdaten = with_retry(
            client.bewegungsdaten,
            config,
            zaehlpunktnummer=config["ZP"],
            date_from=start_date,
            date_until=end_date,
            aggregat="NONE"
        )
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        sys.exit(1)
    
    # Process the data - create individual 15-minute delta values
    statistics = []
    
    logger.info(f"Processing {len(bewegungsdaten.get('values', []))} data points")
    
    for entry in bewegungsdaten.get("values", []):
        try:
            ts = datetime.fromisoformat(entry["zeitpunktVon"].replace("Z", "+00:00"))
            # Convert wert to float - this is the 15-minute consumption delta
            value_kwh = float(entry["wert"])
            
            statistics.append({
                "start": ts.isoformat(),
                "delta": value_kwh,  # This is the actual 15-minute consumption
                "timestamp": ts.isoformat()
            })
            logger.debug(f"Processed 15-min interval: {ts.isoformat()} = {value_kwh} kWh")
        except (KeyError, ValueError) as e:
            logger.warning(f"Error processing entry {entry}: {e}")
    
    # Publish MQTT discovery for Home Assistant integration
    publish_mqtt_discovery(config)
    
    # Publish data to MQTT
    publish_mqtt_data(statistics, config)
    
    logger.info("==== Wiener Netze Smart Meter Sync completed ====")

def fetch_bewegungsdaten(config):
    """
    Fetch energy consumption data from Wiener Netze API.
    
    Args:
        config (dict): Configuration dictionary with credentials and settings
        
    Returns:
        list: List of statistics dictionaries containing energy data
    """
    # Import the vienna-smartmeter library
    from vienna_smartmeter import Smartmeter
    import inspect
    
    # Helper function to inspect the Smartmeter class
    def inspect_smartmeter_class():
        """Inspect the Smartmeter class to help with debugging."""
        try:
            # Get all methods of the Smartmeter class
            methods = inspect.getmembers(Smartmeter, predicate=inspect.isfunction)
            logger.debug(f"Available methods in Smartmeter class: {[m[0] for m in methods]}")
            
            # Try to get the signature of the bewegungsdaten method
            if hasattr(Smartmeter, 'bewegungsdaten'):
                sig = inspect.signature(Smartmeter.bewegungsdaten)
                logger.debug(f"Signature of bewegungsdaten method: {sig}")
            else:
                logger.warning("bewegungsdaten method not found in Smartmeter class")
        except Exception as e:
            logger.error(f"Error inspecting Smartmeter class: {e}")
    
    try:
        # Check if we should use mock data
        use_mock = config.get("USE_MOCK_DATA", False)
        
        # Initialize the client
        logger.info("Initializing Wiener Netze Smartmeter client")
        client = Smartmeter(
            username=config.get("WNSM_USERNAME", config.get("USERNAME")),
            password=config.get("WNSM_PASSWORD", config.get("PASSWORD"))
        )
        
        # Inspect the Smartmeter class if debug is enabled
        if config.get("DEBUG", False):
            inspect_smartmeter_class()
        
        # Login to the service
        logger.info("Logging in to Wiener Netze service")
        
        # Fetch the data
        zp = config.get("ZP")
        days = int(config.get("HISTORY_DAYS", 1))
        
        # Fetch data from API
        from datetime import date, timedelta, datetime
        
        # Use yesterday as the end date since data is only available until the previous day
        date_until = date.today() - timedelta(days=1)
        logger.info(f"Using yesterday ({date_until}) as end date since data is only available until the previous day")
        
        # Calculate start date based on history_days
        date_from = date_until - timedelta(days=days-1)  # -1 because we want to include the end date
        
        logger.info(f"Fetching data from {date_from} to {date_until} ({days} days)")
        
        # Get zaehlpunkte if ZP is not provided
        if not zp:
            logger.info("No ZP provided, fetching zaehlpunkte")
            zaehlpunkte = client.zaehlpunkte()
            if zaehlpunkte and len(zaehlpunkte) > 0:
                # Get the first zaehlpunkt
                zp = zaehlpunkte[0]["zaehlpunkte"][0]["zaehlpunktnummer"]
                logger.info(f"Using zaehlpunkt: {zp}")
            else:
                logger.error("No zaehlpunkte found")
                return []
        
        # Use the bewegungsdaten method to fetch data
        logger.info(f"Fetching bewegungsdaten for zaehlpunkt {zp}")
        try:
            # Try to fetch with granularity parameter (for 15-min intervals)
            try:
                raw_data = client.bewegungsdaten(
                    zaehlpunkt=zp,
                    date_from=date_from,
                    date_to=date_until,
                    granularity="QH"  # QH = Quarter Hour
                )
                logger.info("Successfully fetched data with granularity=QH parameter")
            except TypeError as e:
                if "unexpected keyword argument 'granularity'" in str(e):
                    logger.info("API doesn't support granularity parameter, trying without it")
                    raw_data = client.bewegungsdaten(
                        zaehlpunkt=zp,
                        date_from=date_from,
                        date_to=date_until
                    )
                else:
                    raise
            
            # Log the structure of the returned data for debugging
            logger.debug(f"Raw data structure: {type(raw_data)}")
            if isinstance(raw_data, dict):
                logger.debug(f"Raw data keys: {raw_data.keys()}")
                
            # Process the data into the expected format
            statistics = process_bewegungsdaten_response(raw_data, config)
            
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                logger.info("Trying alternative parameter names for bewegungsdaten method")
                # Try with zaehlpunktnummer parameter (older versions)
                raw_data = client.bewegungsdaten(
                    zp,  # positional argument
                    date_from=date_from,
                    date_to=date_until
                )
                
                # Process the data into the expected format
                statistics = process_bewegungsdaten_response(raw_data, config)
            else:
                raise
        
        return statistics
    except TypeError as e:
        logger.error(f"Type error in API call: {e}")
        logger.exception(e)  # Log the full exception traceback
        
        # Check if this is a method signature issue
        if "unexpected keyword argument" in str(e) or "missing required positional argument" in str(e):
            logger.warning("API method signature mismatch. This might be due to a version mismatch between the addon and the vienna-smartmeter library.")
            logger.info("Please check the addon logs and report this issue to the addon maintainer.")
        
        # If mock data is enabled, return mock data
        if config.get("USE_MOCK_DATA", False):
            logger.info("Using mock data as fallback")
            return _generate_mock_data(date_from, date_until)
        
        return []
    except AttributeError as e:
        logger.error(f"Attribute error in API call: {e}")
        logger.exception(e)  # Log the full exception traceback
        
        # Check if this is a missing method issue
        if "has no attribute 'bewegungsdaten'" in str(e):
            logger.warning("The installed vienna-smartmeter library doesn't have the bewegungsdaten method.")
            logger.info("Attempting to implement bewegungsdaten functionality directly...")
            
            try:
                # Try to implement the bewegungsdaten functionality directly
                # This is a fallback for older versions of the library
                customer_id = client.profil()["defaultGeschaeftspartnerRegistration"]["geschaeftspartner"]
                
                # Format dates for the API
                date_from_str = date_from.strftime("%Y-%m-%d")
                date_to_str = date_until.strftime("%Y-%m-%d")
                
                # Construct the endpoint URL
                endpoint = f"messdaten/{customer_id}/{zp}/bewegungsdaten"
                
                # Make the API request
                logger.info(f"Making direct API request to {endpoint}")
                response = client._request(
                    endpoint,
                    params={
                        "dateFrom": date_from_str,
                        "dateTo": date_to_str
                    }
                )
                
                logger.info("Successfully fetched bewegungsdaten using direct API call")
                return response
            except Exception as fallback_error:
                logger.error(f"Fallback implementation failed: {fallback_error}")
                logger.exception(fallback_error)
        else:
            logger.warning("Unexpected attribute error. Please report this issue to the addon maintainer.")
        
        # If mock data is enabled, return mock data
        if config.get("USE_MOCK_DATA", False):
            logger.info("Using mock data as fallback")
            return _generate_mock_data(date_from, date_until)
        
        return []
    except Exception as e:
        logger.error(f"Error fetching Bewegungsdaten: {e}")
        logger.exception(e)  # Log the full exception traceback
        
        # If mock data is enabled, return mock data
        if config.get("USE_MOCK_DATA", False):
            logger.info("Using mock data as fallback")
            return _generate_mock_data(date_from, date_until)
        
        return []

def process_bewegungsdaten_response(raw_data, config=None):
    """
    Process the response from the bewegungsdaten method into a standardized format.
    
    Args:
        raw_data: The raw data returned by the bewegungsdaten method
        config: Configuration dictionary, used for fallback options
        
    Returns:
        list: A list of dictionaries with standardized format
    """
    # Default config if none provided
    if config is None:
        config = {}
    logger.debug(f"Processing bewegungsdaten response of type: {type(raw_data)}")
    
    # Initialize an empty list for the processed data
    processed_data = []
    
    try:
        # Handle different response formats
        if isinstance(raw_data, dict):
            # Format 1: Dictionary with 'data' key containing a list of data points
            if 'data' in raw_data and isinstance(raw_data['data'], list):
                logger.info(f"Processing data in format 1 with {len(raw_data['data'])} data points")
                
                # Convert each data point to the expected format
                for point in raw_data['data']:
                    if isinstance(point, dict) and 'timestamp' in point and 'value' in point:
                        processed_data.append({
                            "start": point['timestamp'],
                            "sum": float(point['value']),
                            "state": float(point['value'])
                        })
            
            # Format 2: Dictionary with 'descriptor' and 'values' keys
            elif 'descriptor' in raw_data and 'values' in raw_data:
                logger.info("Processing data in format 2")
                
                # Extract values and convert to the expected format
                values = raw_data.get('values', [])
                
                # Log the values for debugging
                logger.debug(f"Values type: {type(values)}")
                logger.debug(f"Values content: {values}")
                
                if not values:
                    logger.warning("No values found in the response")
                    # Check if there's a message in the descriptor
                    descriptor = raw_data.get('descriptor', {})
                    if isinstance(descriptor, dict):
                        logger.debug(f"Descriptor: {descriptor}")
                        if 'message' in descriptor:
                            logger.warning(f"Message from API: {descriptor['message']}")
                        if 'zeitpunktVon' in descriptor and 'zeitpunktBis' in descriptor:
                            logger.info(f"API data period: {descriptor['zeitpunktVon']} to {descriptor['zeitpunktBis']}")
                
                if isinstance(values, list):
                    running_sum = 0
                    for value in values:
                        # Format 2.1: Dictionary with 'timestamp' and 'value' keys (15-min intervals)
                        if isinstance(value, dict) and 'timestamp' in value and 'value' in value:
                            value_float = float(value['value'])
                            running_sum += value_float
                            processed_data.append({
                                "start": value['timestamp'],
                                "sum": running_sum,
                                "state": value_float
                            })
                        # Format 2.2: Dictionary with 'wert', 'zeitpunktVon', and 'zeitpunktBis' keys (daily data)
                        elif isinstance(value, dict) and 'wert' in value and 'zeitpunktVon' in value and 'zeitpunktBis' in value:
                            value_float = float(value['wert'])
                            running_sum += value_float
                            
                            # Use zeitpunktVon as the timestamp
                            timestamp = value['zeitpunktVon']
                            
                            # Log the daily data
                            logger.info(f"Processing daily data: {timestamp} to {value['zeitpunktBis']}, value: {value_float} kWh")
                            
                            # Create 24 hourly entries to distribute the daily value
                            from datetime import datetime, timedelta
                            try:
                                # Parse the timestamp
                                dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                                
                                # Calculate hourly value (divide by 24 for hourly distribution)
                                hourly_value = value_float / 24
                                
                                # Create 24 hourly entries
                                for hour in range(24):
                                    hour_dt = dt + timedelta(hours=hour)
                                    hour_timestamp = hour_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                                    
                                    processed_data.append({
                                        "start": hour_timestamp,
                                        "sum": running_sum - (value_float - (hourly_value * (hour + 1))),
                                        "state": hourly_value
                                    })
                                
                                logger.info(f"Created {24} hourly entries for daily value {value_float} kWh")
                            except Exception as e:
                                logger.error(f"Error creating hourly entries: {e}")
                                # If we can't create hourly entries, just use the daily value
                                processed_data.append({
                                    "start": timestamp,
                                    "sum": running_sum,
                                    "state": value_float
                                })
                        else:
                            logger.warning(f"Skipping invalid value item: {value}")
            
            # Format 3: Dictionary with other structure
            else:
                logger.warning(f"Unknown dictionary format with keys: {raw_data.keys()}")
                # Try to extract any data we can find
                for key, value in raw_data.items():
                    if isinstance(value, list):
                        logger.info(f"Found list under key '{key}' with {len(value)} items")
                        running_sum = 0
                        for item in value:
                            if isinstance(item, dict):
                                # Look for timestamp and value fields with various possible names
                                timestamp = None
                                value_num = None
                                
                                # Try to find timestamp field
                                for ts_field in ['timestamp', 'time', 'date', 'zeitpunkt', 'zeit']:
                                    if ts_field in item:
                                        timestamp = item[ts_field]
                                        break
                                
                                # Try to find value field
                                for val_field in ['value', 'wert', 'verbrauch', 'consumption']:
                                    if val_field in item:
                                        try:
                                            value_num = float(item[val_field])
                                            break
                                        except (ValueError, TypeError):
                                            pass
                                
                                if timestamp and value_num is not None:
                                    running_sum += value_num
                                    processed_data.append({
                                        "start": timestamp,
                                        "sum": running_sum,
                                        "state": value_num
                                    })
        
        # Handle list response
        elif isinstance(raw_data, list):
            logger.info(f"Processing data as list with {len(raw_data)} items")
            running_sum = 0
            for item in raw_data:
                if isinstance(item, dict):
                    # Look for timestamp and value fields with various possible names
                    timestamp = None
                    value_num = None
                    
                    # Try to find timestamp field
                    for ts_field in ['timestamp', 'time', 'date', 'zeitpunkt', 'zeit']:
                        if ts_field in item:
                            timestamp = item[ts_field]
                            break
                    
                    # Try to find value field
                    for val_field in ['value', 'wert', 'verbrauch', 'consumption']:
                        if val_field in item:
                            try:
                                value_num = float(item[val_field])
                                break
                            except (ValueError, TypeError):
                                pass
                    
                    if timestamp and value_num is not None:
                        running_sum += value_num
                        processed_data.append({
                            "start": timestamp,
                            "sum": running_sum,
                            "state": value_num
                        })
        
        logger.info(f"Processed {len(processed_data)} data points")
        
        # If no data was processed but we have a raw_data object, log more details
        if not processed_data and raw_data:
            logger.warning("No data points were processed from the API response")
            if isinstance(raw_data, dict):
                logger.debug(f"Raw data keys: {raw_data.keys()}")
                # Check for error messages or status information
                for key in ['error', 'message', 'status', 'descriptor']:
                    if key in raw_data:
                        logger.warning(f"{key}: {raw_data[key]}")
            
            # If USE_MOCK_DATA is enabled in config, generate mock data
            if config.get("USE_MOCK_DATA", False):
                logger.info("USE_MOCK_DATA is enabled, generating mock data as fallback")
                from datetime import date, timedelta
                today = date.today()
                yesterday = today - timedelta(days=1)
                return _generate_mock_data(yesterday - timedelta(days=6), yesterday)
        
        return processed_data
    
    except Exception as e:
        logger.error(f"Error processing bewegungsdaten response: {e}")
        logger.exception(e)
        return []

def _generate_mock_data(date_from, date_until):
    """Generate mock data for testing purposes."""
    from datetime import datetime, timedelta
    
    # Create a simple mock response with some data
    mock_data = []
    
    # Generate data points every 15 minutes
    current_date = datetime.combine(date_from, datetime.min.time())
    end_date = datetime.combine(date_until, datetime.max.time())
    
    running_sum = 0
    while current_date <= end_date:
        # Generate a random value between 0.1 and 1.0
        import random
        value = round(random.uniform(0.1, 1.0), 3)
        running_sum += value
        
        mock_data.append({
            "start": current_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "sum": running_sum,
            "state": value
        })
        
        # Increment by 15 minutes
        current_date += timedelta(minutes=15)
    
    logger.info(f"Generated {len(mock_data)} mock data points")
    return mock_data

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

