"""Utility functions for core operations."""

import json
import logging
import time
import os
from typing import Callable, Any, Optional
from functools import wraps

from ..config.loader import WNSMConfig
from ..api.client import Smartmeter

logger = logging.getLogger(__name__)


def with_retry(func: Callable, config: WNSMConfig, *args, **kwargs) -> Any:
    """Execute a function with retry logic.
    
    Args:
        func: Function to execute
        config: Configuration object containing retry settings
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function call
        
    Raises:
        Exception: The last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(config.retry_count + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < config.retry_count:
                logger.warning(
                    f"Attempt {attempt + 1}/{config.retry_count + 1} failed: {e}. "
                    f"Retrying in {config.retry_delay} seconds..."
                )
                time.sleep(config.retry_delay)
            else:
                logger.error(f"All {config.retry_count + 1} attempts failed")
    
    if last_exception:
        raise last_exception


class SessionManager:
    """Manages API session persistence."""
    
    def __init__(self, config: WNSMConfig):
        """Initialize session manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.session_file = config.session_file
    
    def save_session(self, client: Smartmeter) -> bool:
        """Save API session to file.
        
        Args:
            client: Smartmeter client instance
            
        Returns:
            True if session was saved successfully, False otherwise
        """
        try:
            session_data = client.export_session()
            if session_data:
                os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
                with open(self.session_file, 'w') as f:
                    json.dump(session_data, f)
                logger.debug(f"Session saved to {self.session_file}")
                return True
            else:
                logger.warning("No session data to save")
                return False
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")
            return False
    
    def load_session(self, client: Smartmeter) -> bool:
        """Load API session from file.
        
        Args:
            client: Smartmeter client instance
            
        Returns:
            True if session was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                client.restore_session(session_data)
                logger.debug(f"Session loaded from {self.session_file}")
                return True
            else:
                logger.debug("No session file found")
                return False
        except Exception as e:
            logger.warning(f"Failed to load session: {e}")
            return False
    
    def clear_session(self) -> bool:
        """Clear saved session file.
        
        Returns:
            True if session was cleared successfully, False otherwise
        """
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                logger.debug("Session file cleared")
            return True
        except Exception as e:
            logger.warning(f"Failed to clear session: {e}")
            return False


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        debug: Enable debug logging if True
    """
    log_level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    if debug:
        logger.debug("Debug logging enabled")