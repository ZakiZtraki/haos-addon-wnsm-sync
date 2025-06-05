"""Pure Python implementation of ha-backfill functionality for Home Assistant OS."""

import logging
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..config.loader import WNSMConfig
from ..data.models import EnergyData, EnergyReading
from .csv_exporter import CSVExporter, CumulativeReading

logger = logging.getLogger(__name__)


class PythonBackfill:
    """Pure Python implementation of backfill functionality.
    
    This eliminates the need for external ha-backfill binary,
    making it suitable for Home Assistant OS.
    """
    
    def __init__(self, config: WNSMConfig):
        """Initialize Python backfill.
        
        Args:
            config: WNSM configuration object
        """
        self.config = config
        self.csv_exporter = CSVExporter()
        
        # Configuration for Home Assistant database
        self.ha_database_path = getattr(config, 'ha_database_path', '/homeassistant/home-assistant_v2.db')
        
        # Metadata IDs for Home Assistant sensors
        self.import_metadata_id = getattr(config, 'ha_import_metadata_id', None)
        self.export_metadata_id = getattr(config, 'ha_export_metadata_id', None)
        self.generation_metadata_id = getattr(config, 'ha_generation_metadata_id', None)
        
        # Short term statistics retention (days)
        self.short_term_days = getattr(config, 'ha_short_term_days', 14)
    
    def backfill_energy_data(self, energy_data: EnergyData) -> bool:
        """Backfill energy data into Home Assistant database.
        
        Args:
            energy_data: Energy data to backfill
            
        Returns:
            True if backfill was successful, False otherwise
        """
        if not self._check_prerequisites():
            return False
        
        try:
            logger.info(f"Starting Python backfill for {len(energy_data.readings)} energy readings")
            
            # Convert readings to cumulative format
            cumulative_readings = self._convert_to_cumulative(energy_data.readings)
            
            if not cumulative_readings:
                logger.warning("No cumulative readings to backfill")
                return False
            
            # Insert data directly into database
            success = self._insert_statistics(cumulative_readings)
            
            if success:
                logger.info("Successfully backfilled energy data to Home Assistant")
            else:
                logger.error("Failed to backfill energy data")
            
            return success
            
        except Exception as e:
            logger.error(f"Error during Python backfill process: {e}")
            return False
    
    def _check_prerequisites(self) -> bool:
        """Check if all prerequisites for backfill are met.
        
        Returns:
            True if prerequisites are met, False otherwise
        """
        # Check if Home Assistant database exists
        if not Path(self.ha_database_path).exists():
            logger.error(f"Home Assistant database not found at {self.ha_database_path}")
            return False
        
        # Check if metadata ID is configured or can be auto-detected
        if not self.import_metadata_id:
            logger.info("No import metadata_id configured, attempting auto-detection...")
            auto_detected_id = self.auto_detect_sensor_metadata_id()
            if auto_detected_id:
                self.import_metadata_id = auto_detected_id
                logger.info(f"Auto-detected sensor metadata_id: {auto_detected_id}")
            else:
                logger.error("Could not auto-detect sensor metadata_id")
                logger.info("Please set 'ha_import_metadata_id' in your configuration")
                logger.info("Or run 'python backfill_setup.py test' to find available sensors")
                return False
        
        logger.debug("All prerequisites for Python backfill are met")
        return True
    
    def _convert_to_cumulative(self, readings: List[EnergyReading]) -> List[CumulativeReading]:
        """Convert delta readings to cumulative readings.
        
        Args:
            readings: List of delta readings
            
        Returns:
            List of cumulative readings
        """
        cumulative_readings = []
        cumulative_total = 0.0
        
        # Sort readings by timestamp to ensure proper cumulative calculation
        sorted_readings = sorted(readings, key=lambda r: r.timestamp)
        
        for reading in sorted_readings:
            cumulative_total += reading.value_kwh
            cumulative_readings.append(
                CumulativeReading(
                    timestamp=reading.timestamp,
                    cumulative_kwh=cumulative_total,
                    quality=reading.quality
                )
            )
        
        return cumulative_readings
    
    def _insert_statistics(self, readings: List[CumulativeReading]) -> bool:
        """Insert statistics directly into Home Assistant database.
        
        Args:
            readings: List of cumulative readings to insert
            
        Returns:
            True if insertion was successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.ha_database_path)
            cursor = conn.cursor()
            
            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Get time range for deletion
            if readings:
                start_time = min(r.timestamp for r in readings)
                end_time = max(r.timestamp for r in readings)
                
                # Delete existing records in the time range
                self._delete_existing_records(cursor, start_time, end_time)
                
                # Insert new records
                self._insert_new_records(cursor, readings)
            
            # Commit transaction
            conn.commit()
            conn.close()
            
            logger.info(f"Successfully inserted {len(readings)} statistics records")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting statistics: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    def _delete_existing_records(self, cursor: sqlite3.Cursor, start_time: datetime, end_time: datetime) -> None:
        """Delete existing records in the specified time range.
        
        Args:
            cursor: Database cursor
            start_time: Start of time range
            end_time: End of time range
        """
        # Convert to UTC timestamps
        start_utc = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_utc = end_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Delete from statistics table
        cursor.execute("""
            DELETE FROM statistics 
            WHERE metadata_id = ? AND start >= ? AND start <= ?
        """, (self.import_metadata_id, start_utc, end_utc))
        
        deleted_long = cursor.rowcount
        logger.debug(f"Deleted {deleted_long} existing long-term statistics records")
        
        # Delete from statistics_short_term table
        cursor.execute("""
            DELETE FROM statistics_short_term 
            WHERE metadata_id = ? AND start >= ? AND start <= ?
        """, (self.import_metadata_id, start_utc, end_utc))
        
        deleted_short = cursor.rowcount
        logger.debug(f"Deleted {deleted_short} existing short-term statistics records")
    
    def _insert_new_records(self, cursor: sqlite3.Cursor, readings: List[CumulativeReading]) -> None:
        """Insert new statistics records.
        
        Args:
            cursor: Database cursor
            readings: List of cumulative readings to insert
        """
        short_term_cutoff = datetime.now() - timedelta(days=self.short_term_days)
        
        for reading in readings:
            # Convert to UTC
            utc_time = reading.timestamp
            
            # Insert into long-term statistics (hourly data)
            if utc_time.minute == 0:  # Only on the hour
                self._insert_statistic_record(
                    cursor, 
                    "statistics", 
                    reading, 
                    utc_time, 
                    utc_time - timedelta(hours=1)
                )
            
            # Insert into short-term statistics (5-minute data)
            if utc_time > short_term_cutoff:
                self._insert_statistic_record(
                    cursor, 
                    "statistics_short_term", 
                    reading, 
                    utc_time, 
                    utc_time - timedelta(minutes=5)
                )
    
    def _insert_statistic_record(
        self, 
        cursor: sqlite3.Cursor, 
        table: str, 
        reading: CumulativeReading, 
        created_time: datetime, 
        start_time: datetime
    ) -> None:
        """Insert a single statistic record.
        
        Args:
            cursor: Database cursor
            table: Table name (statistics or statistics_short_term)
            reading: Cumulative reading
            created_time: Record creation time
            start_time: Start time for the statistic period
        """
        # Format timestamps for SQLite
        created_str = (created_time + timedelta(seconds=10)).strftime('%Y-%m-%d %H:%M:%S')
        start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(f"""
            INSERT INTO {table} (created, start, state, sum, metadata_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            created_str,
            start_str,
            reading.cumulative_kwh,  # state (current reading)
            reading.cumulative_kwh,  # sum (cumulative total)
            self.import_metadata_id
        ))
    
    def get_sensor_metadata_ids(self) -> Dict[str, Any]:
        """Get sensor metadata IDs from Home Assistant database.
        
        Returns:
            Dictionary with sensor information
        """
        logger.debug("--- Querying Database for All Energy Sensors ---")
        try:
            logger.debug(f"Connecting to database: {self.ha_database_path}")
            conn = sqlite3.connect(self.ha_database_path)
            cursor = conn.cursor()
            
            # Query statistics_meta table for energy sensors
            logger.debug("Executing query for all kWh sensors...")
            cursor.execute("""
                SELECT id, statistic_id, source, unit_of_measurement, name
                FROM statistics_meta
                WHERE unit_of_measurement = 'kWh'
                ORDER BY statistic_id
            """)
            
            rows = cursor.fetchall()
            logger.debug(f"Query returned {len(rows)} rows")
            
            sensors = []
            for row in rows:
                sensor_data = {
                    'metadata_id': row[0],
                    'statistic_id': row[1],
                    'source': row[2],
                    'unit': row[3],
                    'name': row[4]
                }
                sensors.append(sensor_data)
                logger.debug(f"Found sensor: {sensor_data}")
            
            conn.close()
            
            logger.info(f"Found {len(sensors)} energy sensors in Home Assistant database:")
            for sensor in sensors:
                logger.info(f"  ID: {sensor['metadata_id']}, Entity: {sensor['statistic_id']}")
            
            logger.debug("--- Database Query Complete ---")
            return {'sensors': sensors}
            
        except Exception as e:
            logger.error(f"Error querying Home Assistant database: {e}")
            return {'sensors': [], 'error': str(e)}
    
    def auto_detect_sensor_metadata_id(self) -> Optional[str]:
        """Automatically detect the metadata ID for the WNSM energy sensor.
        
        This looks for the sensor created by this addon's MQTT discovery.
        
        Returns:
            Metadata ID if found, None otherwise
        """
        logger.debug("--- Starting Auto-Detection ---")
        try:
            # Get the expected sensor name based on Zählpunkt
            zp_suffix = self.config.zp[-8:] if hasattr(self.config, 'zp') and self.config.zp else None
            logger.debug(f"Zählpunkt from config: {getattr(self.config, 'zp', 'NOT_SET')}")
            logger.debug(f"Zählpunkt suffix: {zp_suffix}")
            
            if not zp_suffix:
                logger.warning("No Zählpunkt configured, cannot auto-detect sensor")
                return None
            
            # Expected sensor entity IDs created by this addon
            expected_sensors = [
                f"sensor.wnsm_daily_total_{zp_suffix}",  # Daily total sensor (preferred for backfill)
                f"sensor.wnsm_energy_{zp_suffix}",      # 15min energy sensor (alternative)
            ]
            logger.debug(f"Expected sensor names: {expected_sensors}")
            
            logger.debug("Connecting to Home Assistant database for auto-detection...")
            conn = sqlite3.connect(self.ha_database_path)
            cursor = conn.cursor()
            
            # Look for our sensors in the statistics_meta table
            logger.debug("Searching for expected sensors in statistics_meta table...")
            for sensor_id in expected_sensors:
                logger.debug(f"Looking for sensor: {sensor_id}")
                cursor.execute("""
                    SELECT id, statistic_id, source, unit_of_measurement, name
                    FROM statistics_meta
                    WHERE statistic_id = ? AND unit_of_measurement = 'kWh'
                """, (sensor_id,))
                
                result = cursor.fetchone()
                if result:
                    metadata_id = str(result[0])
                    logger.info(f"Auto-detected WNSM sensor: {sensor_id} (metadata_id: {metadata_id})")
                    logger.debug("--- Auto-Detection Successful ---")
                    conn.close()
                    return metadata_id
                else:
                    logger.debug(f"Sensor {sensor_id} not found in database")
            
            conn.close()
            
            # If not found, log available sensors for debugging
            logger.warning(f"Could not auto-detect WNSM sensor. Expected one of: {expected_sensors}")
            logger.debug("Getting list of all available sensors for debugging...")
            sensor_info = self.get_sensor_metadata_ids()
            if sensor_info.get('sensors'):
                logger.info("Available energy sensors:")
                for sensor in sensor_info['sensors']:
                    logger.info(f"  {sensor['statistic_id']} (ID: {sensor['metadata_id']})")
            else:
                logger.warning("No energy sensors found in database at all!")
            
            logger.debug("--- Auto-Detection Failed ---")
            return None
            
        except Exception as e:
            logger.error(f"Error auto-detecting sensor metadata ID: {e}")
            return None
    
    def test_backfill_setup(self) -> Dict[str, Any]:
        """Test the backfill setup and return diagnostic information.
        
        Returns:
            Dictionary with test results and diagnostic information
        """
        results = {
            'python_backfill_available': True,  # Always true for Python implementation
            'ha_database_exists': Path(self.ha_database_path).exists(),
            'import_metadata_id_configured': bool(self.import_metadata_id),
            'csv_export_directory': str(self.csv_exporter.output_dir),
            'csv_export_directory_writable': self.csv_exporter.output_dir.exists() and 
                                           self.csv_exporter.output_dir.is_dir(),
            'database_path': self.ha_database_path
        }
        
        # Test auto-detection if database exists and no metadata ID is configured
        if results['ha_database_exists'] and not self.import_metadata_id:
            auto_detected_id = self.auto_detect_sensor_metadata_id()
            results['auto_detected_metadata_id'] = auto_detected_id
            results['auto_detection_available'] = bool(auto_detected_id)
            if auto_detected_id:
                results['import_metadata_id_configured'] = True  # Consider it configured if auto-detected
        else:
            results['auto_detection_available'] = False
        
        # Get sensor information
        sensor_info = self.get_sensor_metadata_ids()
        results.update(sensor_info)
        
        # Overall status
        results['ready_for_backfill'] = all([
            results['python_backfill_available'],
            results['ha_database_exists'],
            results['import_metadata_id_configured'],
            results['csv_export_directory_writable']
        ])
        
        return results
    
    def create_test_data(self, days: int = 2) -> EnergyData:
        """Create test energy data for testing purposes.
        
        Args:
            days: Number of days of test data to create
            
        Returns:
            EnergyData object with test readings
        """
        readings = []
        base_time = datetime.now() - timedelta(days=days)
        
        # Generate 15-minute readings for the specified number of days
        total_intervals = days * 24 * 4  # 4 intervals per hour
        
        for i in range(total_intervals):
            timestamp = base_time + timedelta(minutes=15 * i)
            # Simulate realistic energy consumption (0.2-0.4 kWh per 15 min)
            value_kwh = 0.2 + (i % 8) * 0.025  # Varies between 0.2 and 0.375
            
            reading = EnergyReading(
                timestamp=timestamp,
                value_kwh=value_kwh,
                quality="good"
            )
            readings.append(reading)
        
        return EnergyData(
            readings=readings,
            zaehlpunkt="AT0010000000000000000000001234567890",
            date_from=base_time,
            date_until=base_time + timedelta(days=days)
        )