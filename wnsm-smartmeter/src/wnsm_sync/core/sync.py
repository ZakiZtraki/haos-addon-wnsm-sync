"""Main synchronization orchestration."""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ..config.loader import WNSMConfig
from ..api.client import Smartmeter
from ..data.processor import DataProcessor
from ..data.models import EnergyData
from ..mqtt.client import MQTTClient
from ..mqtt.discovery import HomeAssistantDiscovery
from .utils import with_retry, SessionManager

logger = logging.getLogger(__name__)


class WNSMSync:
    """Main synchronization orchestrator for WNSM data."""
    
    def __init__(self, config: WNSMConfig):
        """Initialize WNSM sync.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.session_manager = SessionManager(config)
        self.data_processor = DataProcessor()
        self.mqtt_client = MQTTClient(config)
        self.discovery = HomeAssistantDiscovery(config)
        self._api_client: Optional[Smartmeter] = None
    
    @property
    def api_client(self) -> Smartmeter:
        """Get or create API client instance."""
        if self._api_client is None:
            self._api_client = Smartmeter(
                username=self.config.wnsm_username,
                password=self.config.wnsm_password,
                use_mock=self.config.use_mock_data,
                api_timeout=self.config.api_timeout,
                use_oauth=getattr(self.config, 'use_oauth', True)
            )
            # Try to load existing session
            self.session_manager.load_session(self._api_client)
        return self._api_client
    
    def setup_discovery(self) -> bool:
        """Setup Home Assistant MQTT discovery.
        
        Returns:
            True if all discovery configs were published successfully
        """
        logger.info("Setting up Home Assistant MQTT discovery")
        
        discovery_configs = self.discovery.get_all_discovery_configs()
        success_count = 0
        
        for discovery_config in discovery_configs:
            if self.mqtt_client.publish_discovery(discovery_config):
                success_count += 1
            else:
                logger.error(f"Failed to publish discovery config: {discovery_config['topic']}")
        
        total_configs = len(discovery_configs)
        logger.info(f"Published {success_count}/{total_configs} discovery configurations")
        
        return success_count == total_configs
    
    def fetch_energy_data(self) -> Optional[EnergyData]:
        """Fetch energy data from the API.
        
        Returns:
            EnergyData object if successful, None otherwise
        """
        if self.config.use_mock_data:
            return self._fetch_mock_data()
        else:
            return self._fetch_real_data()
    
    def _fetch_mock_data(self) -> EnergyData:
        """Generate mock energy data for testing."""
        logger.info("Generating mock energy data")
        
        # Generate data for the last N days
        date_until = datetime.now()
        date_from = date_until - timedelta(days=self.config.history_days)
        
        return self.data_processor.generate_mock_data(
            date_from=date_from,
            date_until=date_until,
            zaehlpunkt=self.config.zp
        )
    
    def _fetch_real_data(self) -> Optional[EnergyData]:
        """Fetch real energy data from the API."""
        try:
            logger.info("Fetching energy data from Wiener Netze API")
            
            # Ensure we're logged in
            if not self.api_client.is_logged_in():
                logger.info("Logging in to Wiener Netze API")
                with_retry(self.api_client.login, self.config)
                # Save session after successful login
                self.session_manager.save_session(self.api_client)
            
            # Calculate date range
            date_until = datetime.now()
            date_from = date_until - timedelta(days=self.config.history_days)
            
            logger.info(f"Fetching bewegungsdaten from {date_from.date()} to {date_until.date()}")
            
            # Fetch bewegungsdaten
            raw_data = with_retry(
                self.api_client.bewegungsdaten,
                self.config,
                zaehlpunktnummer=self.config.zp,
                date_from=date_from,
                date_until=date_until
            )
            
            if not raw_data:
                logger.warning("No data returned from API")
                return None
            
            # Process the raw data
            energy_data = self.data_processor.process_bewegungsdaten_response(
                raw_data, self.config.zp
            )
            
            if energy_data:
                logger.info(
                    f"Successfully fetched {energy_data.reading_count} readings, "
                    f"total: {energy_data.total_kwh:.3f} kWh"
                )
            
            return energy_data
            
        except Exception as e:
            logger.error(f"Failed to fetch energy data: {e}")
            # Clear session on authentication errors
            if "auth" in str(e).lower() or "login" in str(e).lower():
                logger.info("Clearing session due to authentication error")
                self.session_manager.clear_session()
                if self._api_client:
                    self._api_client.reset()
            return None
    
    def publish_energy_data(self, energy_data: EnergyData) -> bool:
        """Publish energy data to MQTT.
        
        Args:
            energy_data: Energy data to publish
            
        Returns:
            True if all data was published successfully
        """
        logger.info(f"Publishing {energy_data.reading_count} energy readings to MQTT")
        
        success_count = 0
        total_readings = len(energy_data.readings)
        
        # Publish individual 15-minute readings
        for reading in energy_data.readings:
            topic = f"{self.config.mqtt_topic}/15min"
            payload = reading.to_mqtt_payload()
            
            if self.mqtt_client.publish_message(topic, payload):
                success_count += 1
            else:
                logger.warning(f"Failed to publish reading for {reading.timestamp}")
        
        # Publish daily total
        self._publish_daily_total(energy_data)
        
        logger.info(f"Published {success_count}/{total_readings} energy readings")
        return success_count == total_readings
    
    def _publish_daily_total(self, energy_data: EnergyData) -> bool:
        """Publish daily total energy consumption.
        
        Args:
            energy_data: Energy data to summarize
            
        Returns:
            True if published successfully
        """
        topic = f"{self.config.mqtt_topic}/daily_total"
        payload = {
            "total": energy_data.total_kwh,
            "date": energy_data.date_from.date().isoformat(),
            "reading_count": energy_data.reading_count
        }
        
        return self.mqtt_client.publish_message(topic, payload)
    
    def publish_status(self, status: str, error: Optional[str] = None) -> bool:
        """Publish sync status to MQTT.
        
        Args:
            status: Current status (e.g., "running", "success", "error")
            error: Error message if status is "error"
            
        Returns:
            True if published successfully
        """
        topic = f"{self.config.mqtt_topic}/status"
        payload = {
            "status": status,
            "last_sync": datetime.now().isoformat(),
            "next_sync": (datetime.now() + timedelta(seconds=self.config.update_interval)).isoformat(),
            "error": error
        }
        
        return self.mqtt_client.publish_message(topic, payload, retain=True)
    
    def publish_availability(self, available: bool = True) -> bool:
        """Publish availability status to MQTT.
        
        Args:
            available: Whether the service is available
            
        Returns:
            True if published successfully
        """
        topic = f"{self.config.mqtt_topic}/availability"
        payload = "online" if available else "offline"
        
        # Publish as plain string, not JSON
        try:
            import paho.mqtt.publish as publish
            
            auth = None
            if self.config.mqtt_username and self.config.mqtt_password:
                auth = {
                    "username": self.config.mqtt_username,
                    "password": self.config.mqtt_password
                }
            
            publish.single(
                topic=topic,
                payload=payload,
                hostname=self.mqtt_client._hostname,
                port=self.mqtt_client._port,
                auth=auth,
                retain=True  # Retain availability messages
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to publish availability: {e}")
            return False
    
    def run_sync_cycle(self) -> bool:
        """Run a single synchronization cycle.
        
        Returns:
            True if sync was successful, False otherwise
        """
        try:
            logger.info("Starting sync cycle")
            self.publish_status("running")
            self.publish_availability(True)
            
            # Fetch energy data
            energy_data = self.fetch_energy_data()
            if not energy_data:
                self.publish_status("error", "Failed to fetch energy data")
                return False
            
            # Publish energy data
            if not self.publish_energy_data(energy_data):
                self.publish_status("error", "Failed to publish some energy data")
                return False
            
            # Mark as successful
            self.publish_status("success")
            logger.info("Sync cycle completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Sync cycle failed: {e}")
            self.publish_status("error", str(e))
            return False
    
    def run_continuous(self) -> None:
        """Run continuous synchronization loop."""
        logger.info("Starting continuous synchronization")
        
        # Setup discovery once at startup
        self.setup_discovery()
        
        try:
            while True:
                # Run sync cycle
                self.run_sync_cycle()
                
                # Sleep until next cycle
                logger.info(f"Sleeping for {self.config.update_interval} seconds")
                time.sleep(self.config.update_interval)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down")
        except Exception as e:
            logger.error(f"Continuous sync failed: {e}")
            raise
        finally:
            # Mark as offline when shutting down
            self.publish_availability(False)