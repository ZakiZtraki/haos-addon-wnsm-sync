#!/usr/bin/env python3
"""Setup and test script for ha-backfill integration."""

import argparse
import os
import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wnsm_sync.config.loader import ConfigLoader
from wnsm_sync.config.secrets import SecretsManager
from wnsm_sync.backfill.ha_backfill import HABackfillIntegration

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_test_config(config_path: str):
    """Load configuration for testing purposes."""
    from wnsm_sync.config.loader import WNSMConfig
    
    # Try to load from file if it exists
    config_data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config file {config_path}: {e}")
    
    # Create minimal config for testing
    test_config = WNSMConfig(
        wnsm_username=config_data.get('WNSM_USERNAME', 'test_user'),
        wnsm_password=config_data.get('WNSM_PASSWORD', 'test_password'),
        zp=config_data.get('ZP', 'AT0010000000000000000000001234567890'),
        mqtt_host=config_data.get('MQTT_HOST', 'localhost'),
        mqtt_port=config_data.get('MQTT_PORT', 1883),
        enable_backfill=config_data.get('ENABLE_BACKFILL', False),
        use_python_backfill=config_data.get('USE_PYTHON_BACKFILL', True),
        ha_database_path=config_data.get('HA_DATABASE_PATH', '/config/home-assistant_v2.db'),
        ha_backfill_binary=config_data.get('HA_BACKFILL_BINARY', '/usr/local/bin/ha-backfill'),
        ha_import_metadata_id=config_data.get('HA_IMPORT_METADATA_ID', None),  # Auto-detected if None
        ha_export_metadata_id=config_data.get('HA_EXPORT_METADATA_ID', None),
        ha_generation_metadata_id=config_data.get('HA_GENERATION_METADATA_ID', None),
        ha_short_term_days=config_data.get('HA_SHORT_TERM_DAYS', 14)
    )
    
    return test_config


def test_backfill_setup(config_path: str) -> None:
    """Test the backfill setup and show diagnostic information."""
    try:
        # Load configuration with minimal required fields for testing
        config = load_test_config(config_path)
        
        # Initialize backfill integration
        backfill = HABackfillIntegration(config)
        
        # Run diagnostic tests
        logger.info("Testing backfill setup...")
        results = backfill.test_backfill_setup()
        
        # Display results
        print("\n" + "="*60)
        print("BACKFILL SETUP DIAGNOSTIC RESULTS")
        print("="*60)
        
        print(f"🔧 Backfill method: {results.get('backfill_method', 'Unknown')}")
        
        if results.get('python_backfill_available'):
            print("✅ Python backfill available: True (recommended for Home Assistant OS)")
        else:
            print(f"✅ ha-backfill binary exists: {results['ha_backfill_binary_exists']}")
            if not results['ha_backfill_binary_exists']:
                print(f"  Expected location: {config.ha_backfill_binary}")
                print("  Install from: https://github.com/aamcrae/ha-backfill")
        
        print(f"✅ Home Assistant database exists: {results['ha_database_exists']}")
        if not results['ha_database_exists']:
            print(f"  Expected location: {results.get('database_path', config.ha_database_path)}")
        
        print(f"✅ Import metadata ID configured: {results['import_metadata_id_configured']}")
        if results.get('auto_detection_available'):
            print(f"🔍 Auto-detected metadata ID: {results.get('auto_detected_metadata_id')}")
            print("  ✅ No manual configuration needed!")
        elif not results['import_metadata_id_configured']:
            print("  ⚠️  Set 'ha_import_metadata_id' in your configuration")
            print("  💡 Or let the addon auto-detect it when running on Home Assistant")
        
        print(f"✅ CSV export directory writable: {results['csv_export_directory_writable']}")
        print(f"  Directory: {results['csv_export_directory']}")
        
        print(f"\n🎯 Ready for backfill: {results['ready_for_backfill']}")
        
        # Show available sensors
        if results.get('sensors'):
            print(f"\nAvailable energy sensors in Home Assistant:")
            print("-" * 50)
            for sensor in results['sensors']:
                print(f"  ID: {sensor['metadata_id']:3} | {sensor['statistic_id']}")
                if sensor.get('name'):
                    print(f"      Name: {sensor['name']}")
            
            print(f"\nTo configure backfill, add these to your config:")
            print("  enable_backfill: true")
            if results['sensors']:
                # Suggest the first sensor as import
                first_sensor = results['sensors'][0]
                print(f"  ha_import_metadata_id: \"{first_sensor['metadata_id']}\"")
        
        if results.get('error'):
            print(f"\nDatabase access error: {results['error']}")
            if "unable to open database file" in results['error']:
                print("  This is expected if running outside Home Assistant environment")
        
        # Show next steps based on current status
        print(f"\n📋 NEXT STEPS:")
        print("-" * 30)
        
        if not results['ha_backfill_binary_exists']:
            print("1. Install ha-backfill:")
            print("   python3 backfill_setup.py install")
        
        if not results['ha_database_exists']:
            print("2. Ensure you're running this on your Home Assistant system")
            print("   The database path should be: /config/home-assistant_v2.db")
        
        if not results['import_metadata_id_configured']:
            print("3. Configure your energy sensor metadata ID")
            print("   Run this script on your HA system to find the correct ID")
        
        if results['ready_for_backfill']:
            print("✅ Your system is ready for backfill!")
            print("   You can now enable backfill in your addon configuration")
        else:
            print("⚠️  Complete the steps above to enable backfill functionality")
        
        print("\n" + "="*60)
        
    except Exception as e:
        logger.error(f"Error testing backfill setup: {e}")
        sys.exit(1)


def install_ha_backfill() -> None:
    """Provide instructions for installing ha-backfill."""
    print("\n" + "="*60)
    print("INSTALLING HA-BACKFILL")
    print("="*60)
    print("""
ha-backfill is a Go utility that needs to be compiled and installed.

🏠 FOR HOME ASSISTANT OS (Recommended):

Since Home Assistant OS doesn't allow permanent installations, we recommend
running ha-backfill from a separate system or using the Python implementation.

Option 1: Use Python Implementation (Coming Soon)
   - Pure Python version that doesn't require external binaries
   - Will be integrated directly into this addon

Option 2: External System Approach
   1. Set up ha-backfill on a separate Linux system
   2. Export CSV files from Home Assistant
   3. Process them on the external system
   4. Import SQL back to Home Assistant

Option 3: Home Assistant Add-on Development
   - Create a separate add-on that includes ha-backfill
   - This would allow permanent installation

🐧 FOR REGULAR LINUX SYSTEMS:

1. Install Go:
   # Alpine Linux:
   apk add go git
   
   # Ubuntu/Debian:
   apt update && apt install golang-go git
   
   # CentOS/RHEL:
   yum install golang git

2. Download and compile ha-backfill:
   git clone https://github.com/aamcrae/ha-backfill.git
   cd ha-backfill
   go build -o ha-backfill backfill.go

3. Install the binary:
   sudo cp ha-backfill /usr/local/bin/
   sudo chmod +x /usr/local/bin/ha-backfill

4. Test the installation:
   ha-backfill -h

💡 ALTERNATIVE: Download pre-compiled binary from:
https://github.com/aamcrae/ha-backfill/releases
""")
    print("="*60)


def run_test_backfill(config_path: str) -> None:
    """Run a test backfill with mock data."""
    try:
        # Load configuration with minimal required fields for testing
        config = load_test_config(config_path)
        
        # Enable mock data for testing
        config.use_mock_data = True
        config.history_days = 2  # Generate 2 days of test data
        
        # Initialize backfill integration
        backfill = HABackfillIntegration(config)
        
        logger.info("Generating test data and running Python backfill...")
        
        # Generate test data using Python backfill
        energy_data = backfill.python_backfill.create_test_data(days=2)
        
        logger.info(f"Generated {len(energy_data.readings)} test readings")
        
        # Test backfill
        success = backfill.backfill_energy_data(energy_data)
        
        if success:
            logger.info("✓ Test backfill completed successfully!")
            print("\nCheck your Home Assistant energy dashboard to see the test data.")
        else:
            logger.error("✗ Test backfill failed")
        
    except Exception as e:
        logger.error(f"Error running test backfill: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Setup and test ha-backfill integration")
    parser.add_argument(
        "--config", 
        default="/data/options.json",
        help="Path to configuration file (default: /data/options.json)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test backfill setup")
    test_parser.add_argument(
        "--config", 
        default="/data/options.json",
        help="Path to configuration file (default: /data/options.json)"
    )
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Show installation instructions")
    
    # Run test backfill command
    run_parser = subparsers.add_parser("run-test", help="Run test backfill with mock data")
    run_parser.add_argument(
        "--config", 
        default="/data/options.json",
        help="Path to configuration file (default: /data/options.json)"
    )
    
    args = parser.parse_args()
    
    if args.command == "test":
        test_backfill_setup(args.config)
    elif args.command == "install":
        install_ha_backfill()
    elif args.command == "run-test":
        run_test_backfill(args.config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()