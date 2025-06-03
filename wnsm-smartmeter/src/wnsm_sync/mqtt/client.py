"""MQTT client for publishing energy data."""

import json
import logging
import time
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse

import paho.mqtt.publish as publish

from ..config.loader import WNSMConfig

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT client for publishing energy data to Home Assistant."""
    
    def __init__(self, config: WNSMConfig):
        """Initialize MQTT client.
        
        Args:
            config: WNSM configuration object
        """
        self.config = config
        self._auth = self._prepare_auth()
        self._hostname, self._port = self._parse_mqtt_host()
    
    def _prepare_auth(self) -> Optional[Dict[str, str]]:
        """Prepare MQTT authentication if credentials are provided."""
        if self.config.mqtt_username and self.config.mqtt_password:
            return {
                "username": self.config.mqtt_username,
                "password": self.config.mqtt_password
            }
        return None
    
    def _parse_mqtt_host(self) -> Tuple[str, int]:
        """Parse MQTT host and extract hostname and port.
        
        Returns:
            Tuple of (hostname, port)
        """
        mqtt_host = self.config.mqtt_host
        
        # Handle URLs with protocol
        if "://" in mqtt_host:
            parsed = urlparse(mqtt_host)
            hostname = parsed.hostname or parsed.netloc
            port = parsed.port or self.config.mqtt_port
        else:
            # Handle host:port format
            if ":" in mqtt_host:
                hostname, port_str = mqtt_host.rsplit(":", 1)
                try:
                    port = int(port_str)
                except ValueError:
                    logger.warning(f"Invalid port in MQTT host '{mqtt_host}', using default port")
                    hostname = mqtt_host
                    port = self.config.mqtt_port
            else:
                hostname = mqtt_host
                port = self.config.mqtt_port
        
        logger.debug(f"MQTT connection: {hostname}:{port}")
        return hostname, port
    
    def publish_message(
        self, 
        topic: str, 
        payload: Dict[str, Any], 
        retry_count: Optional[int] = None
    ) -> bool:
        """Publish a message to MQTT broker.
        
        Args:
            topic: MQTT topic to publish to
            payload: Message payload (will be JSON serialized)
            retry_count: Number of retry attempts (uses config default if None)
            
        Returns:
            True if message was published successfully, False otherwise
        """
        if retry_count is None:
            retry_count = self.config.retry_count
        
        json_payload = json.dumps(payload)
        
        for attempt in range(retry_count + 1):
            try:
                logger.debug(f"Publishing to {topic}: {json_payload}")
                
                publish.single(
                    topic=topic,
                    payload=json_payload,
                    hostname=self._hostname,
                    port=self._port,
                    auth=self._auth,
                    retain=False
                )
                
                logger.debug(f"Successfully published to {topic}")
                return True
                
            except Exception as e:
                if attempt < retry_count:
                    logger.warning(
                        f"Failed to publish to {topic} (attempt {attempt + 1}/{retry_count + 1}): {e}"
                    )
                    time.sleep(self.config.retry_delay)
                else:
                    logger.error(f"Failed to publish to {topic} after {retry_count + 1} attempts: {e}")
                    return False
        
        return False
    
    def publish_discovery(self, discovery_config: Dict[str, Any]) -> bool:
        """Publish Home Assistant MQTT discovery configuration.
        
        Args:
            discovery_config: Discovery configuration dictionary
            
        Returns:
            True if published successfully, False otherwise
        """
        topic = discovery_config.get("topic")
        config = discovery_config.get("config", {})
        
        if not topic:
            logger.error("Discovery configuration missing topic")
            return False
        
        logger.info(f"Publishing MQTT discovery configuration to {topic}")
        return self.publish_message(topic, config)
    
    def test_connection(self) -> bool:
        """Test MQTT connection by publishing a test message.
        
        Returns:
            True if connection test successful, False otherwise
        """
        test_topic = f"{self.config.mqtt_topic}/test"
        test_payload = {
            "test": True,
            "timestamp": time.time()
        }
        
        logger.info("Testing MQTT connection...")
        success = self.publish_message(test_topic, test_payload, retry_count=1)
        
        if success:
            logger.info("MQTT connection test successful")
        else:
            logger.error("MQTT connection test failed")
        
        return success