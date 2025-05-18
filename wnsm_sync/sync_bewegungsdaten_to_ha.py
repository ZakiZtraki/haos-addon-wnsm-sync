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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("wnsm_sync")

# === CONFIGURATION ===
# Configuration from environment variables with fallbacks to options.json
def get_config():
    """Load configuration from environment or options.json file."""
    config = {
        "USERNAME": os.getenv("WNSM_USERNAME"),
        "PASSWORD": os.getenv("WNSM_PASSWORD"),
        "HA_URL": os.getenv("HA_URL", "http://homeassistant:8123"),
        "STATISTIC_ID": os.getenv("STAT_ID", "sensor.wiener_netze_energy"),
        "MQTT_HOST": os.getenv("MQTT_HOST", "core-mosquitto"),
        "MQTT_TOPIC": os.getenv("MQTT_TOPIC", "smartmeter/energy/state"),
        "MQTT_USERNAME": os.getenv("MQTT_USERNAME"),
        "MQTT_PASSWORD": os.getenv("MQTT_PASSWORD"),
        "HISTORY_DAYS": int(os.getenv("HISTORY_DAYS", "1")),
        "RETRY_COUNT": int(os.getenv("RETRY_COUNT", "3")),
        "RETRY_DELAY": int(os.getenv("RETRY_DELAY", "10")),
        "SESSION_FILE": os.getenv("SESSION_FILE", "/data/wnsm_session.json")
    }
    
    # If any required values are missing, fall back to options.json
    required_keys = ["USERNAME", "PASSWORD", "ZP"]
    if not all(config.get(key) for key in required_keys):
        logger.info("Some required configuration missing - loading from options.json")
        try:
            with open("/data/options.json") as f:
                opts = json.load(f)
            
            # Map options to config with our specific prefix
            config.update({
                "USERNAME": opts.get("WNSM_USERNAME", config["USERNAME"]),
                "PASSWORD": opts.get("WNSM_PASSWORD", config["PASSWORD"]),
                "GP": opts.get("WNSM_GP", config["GP"]),
                "ZP": opts.get("WNSM_ZP", config["ZP"]),
                "HA_URL": opts.get("HA_URL", config["HA_URL"]),
                "STATISTIC_ID": opts.get("STAT_ID", config["STATISTIC_ID"]),
                "MQTT_USERNAME": opts.get("MQTT_USERNAME", config["MQTT_USERNAME"]),
                "MQTT_PASSWORD": opts.get("MQTT_PASSWORD", config["MQTT_PASSWORD"]),
                "MQTT_HOST": opts.get("MQTT_HOST", config["MQTT_HOST"]),
                "HISTORY_DAYS": int(opts.get("HISTORY_DAYS", config["HISTORY_DAYS"])),
                "RETRY_COUNT": int(opts.get("RETRY_COUNT", config["RETRY_COUNT"])),
                "RETRY_DELAY": int(opts.get("RETRY_DELAY", config["RETRY_DELAY"]))
            })
        except Exception as e:
            logger.error(f"Error loading options.json: {e}")
    
    # Ensure we have the critical values
    for key in required_keys:
        if not config.get(key):
            logger.error(f"Missing required configuration: {key}")
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

def publish_mqtt_discovery(config):
    """Publish MQTT discovery configuration for Home Assistant."""
    try:
        device_id = config["ZP"].lower().replace("0", "")
        publish.single(
            topic=f"homeassistant/sensor/wnsm_sync_{device_id}/config",
            payload=json.dumps({
                "name": "Wiener Netze Smartmeter Sync",
                "state_topic": config["MQTT_TOPIC"],
                "unit_of_measurement": "kWh",
                "device_class": "energy",
                "state_class": "total_increasing",
                "unique_id": f"wnsm_sync_energy_sensor_{device_id}",
                "value_template": "{{ value_json.value }}",
                "timestamp_template": "{{ value_json.timestamp }}",
                "device": {
                    "identifiers": [f"wnsm_sync_{device_id}"],
                    "name": "Wiener Netze Smart Meter",
                    "manufacturer": "Wiener Netze",
                    "model": "Smart Meter"
                }
            }),
            hostname=config["MQTT_HOST"],
            auth={
                "username": config["MQTT_USERNAME"],
                "password": config["MQTT_PASSWORD"]
            },
            retain=True
        )
        logger.info("MQTT discovery configuration published")
    except Exception as e:
        logger.error(f"Failed to publish MQTT discovery: {e}")

def publish_mqtt_data(statistics, config):
    """Publish energy data to MQTT."""
    if not statistics:
        logger.warning("No statistics to publish")
        return
    
    logger.info(f"Publishing {len(statistics)} entries to MQTT")
    
    for s in statistics:
        topic = f"{config['MQTT_TOPIC']}/{s['start'][:16]}"  # e.g. smartmeter/energy/state/2025-05-16T00:15
        payload = {
            "value": s["sum"],
            "timestamp": s["start"]
        }
        
        try:
            publish.single(
                topic=topic,
                payload=json.dumps(payload),
                hostname=config["MQTT_HOST"],
                auth={
                    "username": config["MQTT_USERNAME"],
                    "password": config["MQTT_PASSWORD"]
                },
                retain=True
            )
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
    
    # Publish latest value to main topic for current state
    try:
        latest = statistics[-1]
        publish.single(
            topic=config["MQTT_TOPIC"],
            payload=json.dumps({
                "value": latest["sum"],
                "timestamp": latest["start"]
            }),
            hostname=config["MQTT_HOST"],
            auth={
                "username": config["MQTT_USERNAME"],
                "password": config["MQTT_PASSWORD"]
            },
            retain=True
        )
        logger.info("✅ All entries published to MQTT")
    except Exception as e:
        logger.error(f"Failed to publish latest value: {e}")

def main():
    """Main function to run the sync process."""
    logger.info("==== Wiener Netze Smart Meter Sync starting ====")
    
    # Load configuration
    config = get_config()
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
    
    # Process the data
    total = Decimal(0)
    statistics = []
    
    logger.info(f"Processing {len(bewegungsdaten.get('values', []))} data points")
    
    for entry in bewegungsdaten.get("values", []):
        try:
            ts = datetime.fromisoformat(entry["zeitpunktVon"].replace("Z", "+00:00"))
            value_kwh = Decimal(str(entry["wert"]))
            total += value_kwh
            statistics.append({
                "start": ts.isoformat(),
                "sum": float(total),
                "state": float(value_kwh)
            })
        except (KeyError, ValueError) as e:
            logger.warning(f"Error processing entry {entry}: {e}")
    
    # Publish MQTT discovery for Home Assistant integration
    publish_mqtt_discovery(config)
    
    # Publish data to MQTT
    publish_mqtt_data(statistics, config)
    
    logger.info("==== Wiener Netze Smart Meter Sync completed ====")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
