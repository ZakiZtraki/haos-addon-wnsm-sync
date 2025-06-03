#!/usr/bin/env python3
"""Entry point for the Wiener Netze Smart Meter Home Assistant Add-on."""

import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from wnsm_sync.config.loader import ConfigLoader
from wnsm_sync.config.secrets import SecretsManager
from wnsm_sync.core.sync import WNSMSync
from wnsm_sync.core.utils import setup_logging

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    try:
        # Load configuration
        secrets_manager = SecretsManager()
        config_loader = ConfigLoader(secrets_manager)
        config = config_loader.load()
        
        # Setup logging
        setup_logging(config.debug)
        
        # Log startup information
        logger.info("Wiener Netze Smart Meter Add-on started")
        
        if config.use_mock_data:
            logger.warning("MOCK DATA MODE ENABLED - Using simulated data instead of real API calls")
        
        # Verify required dependencies
        try:
            import vienna_smartmeter
            logger.info("vienna-smartmeter library loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to import vienna-smartmeter: {e}")
            logger.error("Make sure vienna-smartmeter is installed")
            sys.exit(1)
        
        # Create and run sync
        sync = WNSMSync(config)
        sync.run_continuous()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down gracefully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()