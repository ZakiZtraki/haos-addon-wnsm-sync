"""Integration with ha-backfill tool for historical data import."""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

from ..config.loader import WNSMConfig
from ..data.models import EnergyData
from .csv_exporter import CSVExporter
from .python_backfill import PythonBackfill

logger = logging.getLogger(__name__)


class HABackfillIntegration:
    """Integration with ha-backfill tool for importing historical energy data."""
    
    def __init__(self, config: WNSMConfig):
        """Initialize ha-backfill integration.
        
        Args:
            config: WNSM configuration object
        """
        self.config = config
        self.csv_exporter = CSVExporter()
        self.python_backfill = PythonBackfill(config)
        
        # Configuration for ha-backfill
        self.ha_database_path = getattr(config, 'ha_database_path', '/homeassistant/home-assistant_v2.db')
        self.ha_backfill_binary = getattr(config, 'ha_backfill_binary', '/usr/local/bin/ha-backfill')
        
        # Metadata IDs for Home Assistant sensors (these need to be configured)
        self.import_metadata_id = getattr(config, 'ha_import_metadata_id', None)
        self.export_metadata_id = getattr(config, 'ha_export_metadata_id', None)
        self.generation_metadata_id = getattr(config, 'ha_generation_metadata_id', None)
        
        # Prefer Python implementation for Home Assistant OS compatibility
        self.use_python_backfill = getattr(config, 'use_python_backfill', True)
    
    def backfill_energy_data(self, energy_data: EnergyData) -> bool:
        """Backfill energy data into Home Assistant database.
        
        Args:
            energy_data: Energy data to backfill
            
        Returns:
            True if backfill was successful, False otherwise
        """
        # Use Python implementation by default (better for Home Assistant OS)
        if self.use_python_backfill:
            logger.info("Using Python backfill implementation")
            return self.python_backfill.backfill_energy_data(energy_data)
        else:
            logger.info("Using external ha-backfill binary")
            return self._backfill_with_external_tool(energy_data)
    
    def _backfill_with_external_tool(self, energy_data: EnergyData) -> bool:
        """Backfill using external ha-backfill tool.
        
        Args:
            energy_data: Energy data to backfill
            
        Returns:
            True if backfill was successful, False otherwise
        """
        if not self._check_prerequisites():
            return False
        
        try:
            logger.info(f"Starting external backfill for {len(energy_data.readings)} energy readings")
            
            # Export data to CSV files
            csv_files = self.csv_exporter.export_multiple_days(energy_data)
            
            if not csv_files:
                logger.warning("No CSV files were created for backfill")
                return False
            
            # Run ha-backfill tool
            success = self._run_ha_backfill(csv_files)
            
            if success:
                logger.info("Successfully backfilled energy data to Home Assistant")
                # Clean up CSV files after successful backfill
                self._cleanup_csv_files(csv_files)
            else:
                logger.error("Failed to backfill energy data")
                # Keep CSV files for debugging
                logger.info(f"CSV files preserved for debugging: {csv_files}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error during backfill process: {e}")
            return False
    
    def _check_prerequisites(self) -> bool:
        """Check if all prerequisites for external backfill tool are met.
        
        Returns:
            True if prerequisites are met, False otherwise
        """
        # Check if ha-backfill binary exists (only for external tool)
        if not self.use_python_backfill and not os.path.exists(self.ha_backfill_binary):
            logger.error(f"ha-backfill binary not found at {self.ha_backfill_binary}")
            logger.info("Please install ha-backfill from https://github.com/aamcrae/ha-backfill")
            logger.info("Or enable Python backfill with 'use_python_backfill: true'")
            return False
        
        # Check if Home Assistant database exists
        if not os.path.exists(self.ha_database_path):
            logger.error(f"Home Assistant database not found at {self.ha_database_path}")
            return False
        
        # Check if metadata IDs are configured
        if not self.import_metadata_id:
            logger.error("Home Assistant import sensor metadata_id not configured")
            logger.info("Please set 'ha_import_metadata_id' in your configuration")
            return False
        
        logger.debug("All prerequisites for backfill are met")
        return True
    
    def _run_ha_backfill(self, csv_files: list[str]) -> bool:
        """Run the ha-backfill tool with the exported CSV files.
        
        Args:
            csv_files: List of CSV file paths
            
        Returns:
            True if ha-backfill ran successfully, False otherwise
        """
        try:
            # Create temporary directory for CSV files (ha-backfill expects a directory)
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy CSV files to temporary directory
                temp_csv_dir = Path(temp_dir) / "csv"
                temp_csv_dir.mkdir()
                
                for csv_file in csv_files:
                    src_path = Path(csv_file)
                    dst_path = temp_csv_dir / src_path.name
                    dst_path.write_text(src_path.read_text())
                
                # Build ha-backfill command
                cmd = [
                    self.ha_backfill_binary,
                    f"-dir={temp_csv_dir}",
                    f"-import-key={self.import_metadata_id}",
                ]
                
                # Add optional metadata IDs if configured
                if self.export_metadata_id:
                    cmd.append(f"-export-key={self.export_metadata_id}")
                if self.generation_metadata_id:
                    cmd.append(f"-gen-key={self.generation_metadata_id}")
                
                logger.info(f"Running ha-backfill command: {' '.join(cmd)}")
                
                # Run ha-backfill and pipe output to sqlite3
                backfill_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                sqlite_cmd = ["sqlite3", self.ha_database_path]
                sqlite_process = subprocess.Popen(
                    sqlite_cmd,
                    stdin=backfill_process.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Close the stdout of the first process to allow it to receive SIGPIPE
                backfill_process.stdout.close()
                
                # Wait for both processes to complete
                sqlite_output, sqlite_error = sqlite_process.communicate()
                backfill_process.wait()
                
                # Check results
                if backfill_process.returncode != 0:
                    _, backfill_error = backfill_process.communicate()
                    logger.error(f"ha-backfill failed: {backfill_error}")
                    return False
                
                if sqlite_process.returncode != 0:
                    logger.error(f"SQLite execution failed: {sqlite_error}")
                    return False
                
                logger.info("ha-backfill completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error running ha-backfill: {e}")
            return False
    
    def _cleanup_csv_files(self, csv_files: list[str]) -> None:
        """Clean up CSV files after successful backfill.
        
        Args:
            csv_files: List of CSV file paths to clean up
        """
        for csv_file in csv_files:
            try:
                os.remove(csv_file)
                logger.debug(f"Cleaned up CSV file: {csv_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up CSV file {csv_file}: {e}")
    
    def get_sensor_metadata_ids(self) -> Dict[str, Any]:
        """Get sensor metadata IDs from Home Assistant database.
        
        This is a helper method to find the correct metadata_id values
        for your energy sensors.
        
        Returns:
            Dictionary with sensor information
        """
        # Use Python backfill implementation for database queries
        return self.python_backfill.get_sensor_metadata_ids()
    
    def test_backfill_setup(self) -> Dict[str, Any]:
        """Test the backfill setup and return diagnostic information.
        
        Returns:
            Dictionary with test results and diagnostic information
        """
        # Use Python backfill implementation for testing
        if self.use_python_backfill:
            results = self.python_backfill.test_backfill_setup()
            results['backfill_method'] = 'Python (recommended for Home Assistant OS)'
            results['ha_backfill_binary_exists'] = os.path.exists(self.ha_backfill_binary)
        else:
            results = {
                'ha_backfill_binary_exists': os.path.exists(self.ha_backfill_binary),
                'ha_database_exists': os.path.exists(self.ha_database_path),
                'import_metadata_id_configured': bool(self.import_metadata_id),
                'csv_export_directory': str(self.csv_exporter.output_dir),
                'csv_export_directory_writable': os.access(self.csv_exporter.output_dir, os.W_OK),
                'backfill_method': 'External ha-backfill binary'
            }
            
            # Get sensor information
            sensor_info = self.get_sensor_metadata_ids()
            results.update(sensor_info)
            
            # Overall status for external tool
            results['ready_for_backfill'] = all([
                results['ha_backfill_binary_exists'],
                results['ha_database_exists'],
                results['import_metadata_id_configured'],
                results['csv_export_directory_writable']
            ])
        
        return results