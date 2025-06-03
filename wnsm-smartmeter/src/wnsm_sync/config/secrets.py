"""Secrets management for Home Assistant integration."""

import os
import re
import yaml
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manages Home Assistant secrets.yaml integration."""
    
    DEFAULT_SECRETS_PATHS = [
        "/config/secrets.yaml",      # Home Assistant config directory
        "/homeassistant/secrets.yaml",  # Alternative path
        "/data/secrets.yaml"         # Add-on data directory (fallback)
    ]
    
    def __init__(self, secrets_paths: Optional[list] = None):
        """Initialize secrets manager.
        
        Args:
            secrets_paths: List of paths to check for secrets.yaml files.
                          If None, uses default paths.
        """
        self.secrets_paths = secrets_paths or self.DEFAULT_SECRETS_PATHS
        self._secrets = self._load_secrets()
    
    def _load_secrets(self) -> Dict[str, Any]:
        """Load secrets from the first available secrets.yaml file."""
        for secrets_path in self.secrets_paths:
            if os.path.exists(secrets_path):
                try:
                    logger.info(f"Loading secrets from {secrets_path}")
                    with open(secrets_path, 'r') as f:
                        secrets = yaml.safe_load(f) or {}
                    logger.info(f"Loaded {len(secrets)} secrets from {secrets_path}")
                    return secrets
                except Exception as e:
                    logger.warning(f"Failed to load secrets from {secrets_path}: {e}")
                    continue
        
        logger.info("No secrets.yaml file found, secrets support disabled")
        return {}
    
    def resolve_value(self, value: Any) -> Any:
        """Resolve secret references in configuration values.
        
        Supports the following formats:
        - !secret secret_name
        - "!secret secret_name"
        - Simple string values (returned as-is)
        
        Args:
            value: The value to resolve, can be any type
            
        Returns:
            The resolved value, with secret references replaced
        """
        if not isinstance(value, str):
            return value
        
        # Match !secret references (with or without quotes)
        secret_pattern = r'^!secret\s+(\w+)$'
        match = re.match(secret_pattern, value.strip())
        
        if match:
            secret_name = match.group(1)
            if secret_name in self._secrets:
                logger.debug(f"Resolved secret reference: !secret {secret_name}")
                return self._secrets[secret_name]
            else:
                logger.warning(f"Secret '{secret_name}' not found in secrets.yaml")
                return value
        
        return value
    
    def has_secrets(self) -> bool:
        """Check if any secrets are loaded."""
        return bool(self._secrets)
    
    def get_secret(self, name: str) -> Optional[str]:
        """Get a specific secret by name."""
        return self._secrets.get(name)