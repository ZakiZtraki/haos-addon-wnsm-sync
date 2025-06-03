"""Configuration loading and validation."""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .secrets import SecretsManager

logger = logging.getLogger(__name__)


@dataclass
class WNSMConfig:
    """Configuration for WNSM Sync."""
    
    # Required fields
    wnsm_username: str
    wnsm_password: str
    zp: str  # Zählpunkt number
    mqtt_host: str
    
    # Optional fields with defaults
    mqtt_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    mqtt_topic: str = "smartmeter/energy/state"
    update_interval: int = 3600  # 1 hour
    history_days: int = 1
    use_mock_data: bool = False
    retry_count: int = 3
    retry_delay: int = 10
    debug: bool = False
    
    # Advanced options
    session_file: str = "/data/session.json"
    secrets_paths: List[str] = field(default_factory=lambda: [
        "/config/secrets.yaml",
        "/homeassistant/secrets.yaml", 
        "/data/secrets.yaml"
    ])
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate configuration values."""
        if not self.wnsm_username:
            raise ValueError("WNSM username is required")
        if not self.wnsm_password:
            raise ValueError("WNSM password is required")
        if not self.zp:
            raise ValueError("Zählpunkt (ZP) is required")
        if not self.mqtt_host:
            raise ValueError("MQTT host is required")
        
        if self.mqtt_port <= 0 or self.mqtt_port > 65535:
            raise ValueError("MQTT port must be between 1 and 65535")
        
        if self.update_interval < 60:
            raise ValueError("Update interval must be at least 60 seconds")
        
        if self.history_days < 1:
            raise ValueError("History days must be at least 1")


class ConfigLoader:
    """Loads and validates configuration from multiple sources."""
    
    OPTIONS_FILE = "/data/options.json"
    
    # Environment variable mappings
    ENV_MAPPINGS = {
        "wnsm_username": ["WNSM_USERNAME", "USERNAME"],
        "wnsm_password": ["WNSM_PASSWORD", "PASSWORD"],
        "zp": ["WNSM_ZP", "ZP"],
        "mqtt_host": ["MQTT_HOST"],
        "mqtt_port": ["MQTT_PORT"],
        "mqtt_username": ["MQTT_USERNAME"],
        "mqtt_password": ["MQTT_PASSWORD"],
        "mqtt_topic": ["MQTT_TOPIC"],
        "update_interval": ["UPDATE_INTERVAL"],
        "history_days": ["HISTORY_DAYS"],
        "use_mock_data": ["WNSM_USE_MOCK_DATA", "USE_MOCK_DATA"],
        "retry_count": ["RETRY_COUNT"],
        "retry_delay": ["RETRY_DELAY"],
        "debug": ["DEBUG"]
    }
    
    # Fields that should be converted to integers
    INT_FIELDS = {"mqtt_port", "update_interval", "history_days", "retry_count", "retry_delay"}
    
    # Fields that should be converted to booleans
    BOOL_FIELDS = {"use_mock_data", "debug"}
    
    def __init__(self, secrets_manager: Optional[SecretsManager] = None):
        """Initialize config loader.
        
        Args:
            secrets_manager: Optional secrets manager for resolving secret references
        """
        self.secrets_manager = secrets_manager or SecretsManager()
    
    def load(self) -> WNSMConfig:
        """Load configuration from all available sources.
        
        Priority order:
        1. options.json (Home Assistant add-on configuration)
        2. Environment variables
        3. Default values
        
        Returns:
            Validated WNSMConfig instance
        """
        config_dict = {}
        
        # Load from options.json first
        self._load_from_options_file(config_dict)
        
        # Fill in missing values from environment variables
        self._load_from_environment(config_dict)
        
        # Resolve secret references
        self._resolve_secrets(config_dict)
        
        # Convert types
        self._convert_types(config_dict)
        
        # Log configuration (without sensitive data)
        self._log_config(config_dict)
        
        # Create and validate config object
        try:
            return WNSMConfig(**config_dict)
        except TypeError as e:
            # Handle unexpected keyword arguments
            logger.error(f"Invalid configuration parameters: {e}")
            # Filter out unknown parameters
            valid_fields = {f.name for f in WNSMConfig.__dataclass_fields__.values()}
            filtered_config = {k: v for k, v in config_dict.items() if k in valid_fields}
            return WNSMConfig(**filtered_config)
    
    def _load_from_options_file(self, config_dict: Dict[str, Any]):
        """Load configuration from Home Assistant options.json file."""
        if os.path.exists(self.OPTIONS_FILE):
            try:
                logger.info(f"Loading configuration from {self.OPTIONS_FILE}")
                with open(self.OPTIONS_FILE, 'r') as f:
                    options = json.load(f)
                
                logger.debug(f"Loaded options: {', '.join(options.keys())}")
                
                # Convert option keys to lowercase with underscores
                for key, value in options.items():
                    config_key = key.lower().replace('-', '_')
                    config_dict[config_key] = value
                    
            except Exception as e:
                logger.error(f"Failed to load options.json: {e}")
        else:
            logger.warning(f"Options file {self.OPTIONS_FILE} not found, using environment variables")
    
    def _load_from_environment(self, config_dict: Dict[str, Any]):
        """Load missing configuration values from environment variables."""
        for config_key, env_vars in self.ENV_MAPPINGS.items():
            if config_key not in config_dict or not config_dict[config_key]:
                for env_var in env_vars:
                    if env_var in os.environ and os.environ[env_var]:
                        config_dict[config_key] = os.environ[env_var]
                        logger.debug(f"Using environment variable {env_var} for {config_key}")
                        break
    
    def _resolve_secrets(self, config_dict: Dict[str, Any]):
        """Resolve secret references in configuration values."""
        if not self.secrets_manager.has_secrets():
            return
        
        for key, value in config_dict.items():
            config_dict[key] = self.secrets_manager.resolve_value(value)
    
    def _convert_types(self, config_dict: Dict[str, Any]):
        """Convert configuration values to appropriate types."""
        for key, value in config_dict.items():
            if key in self.INT_FIELDS and value is not None:
                try:
                    config_dict[key] = int(value)
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {key}='{value}' to integer")
            
            elif key in self.BOOL_FIELDS and value is not None:
                if isinstance(value, str):
                    config_dict[key] = value.lower() in ("true", "1", "yes", "on")
                else:
                    config_dict[key] = bool(value)
    
    def _log_config(self, config_dict: Dict[str, Any]):
        """Log configuration without sensitive data."""
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Final configuration:")
            for key, value in config_dict.items():
                if 'password' in key.lower():
                    logger.debug(f"  {key}: ****")
                else:
                    logger.debug(f"  {key}: {value}")