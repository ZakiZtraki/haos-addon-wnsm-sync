"""CSV exporter for ha-backfill integration."""

import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from ..data.models import EnergyData, EnergyReading

logger = logging.getLogger(__name__)


class CSVExporter:
    """Exports energy data to CSV format compatible with ha-backfill."""
    
    def __init__(self, output_dir: str = "/tmp/wnsm_backfill"):
        """Initialize CSV exporter.
        
        Args:
            output_dir: Directory to store CSV files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_energy_data(self, energy_data: EnergyData) -> str:
        """Export energy data to CSV file compatible with ha-backfill.
        
        Args:
            energy_data: Energy data to export
            
        Returns:
            Path to the created CSV file
        """
        # Create filename based on date range
        start_date = energy_data.date_from.strftime("%Y-%m-%d")
        end_date = energy_data.date_until.strftime("%Y-%m-%d")
        filename = f"wnsm_energy_{start_date}_to_{end_date}.csv"
        filepath = self.output_dir / filename
        
        logger.info(f"Exporting {len(energy_data.readings)} readings to {filepath}")
        
        # Convert readings to cumulative values (ha-backfill expects cumulative kWh)
        cumulative_readings = self._convert_to_cumulative(energy_data.readings)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header (compatible with ha-backfill format)
            writer.writerow(['#date', 'time', 'IMP', 'EXP', 'GEN-T'])
            
            # Write data rows
            for reading in cumulative_readings:
                date_str = reading.timestamp.strftime("%Y-%m-%d")
                time_str = reading.timestamp.strftime("%H:%M")
                
                # For WNSM data, we only have import (consumption) data
                # Set export and generation to 0 for now
                writer.writerow([
                    date_str,
                    time_str,
                    f"{reading.cumulative_kwh:.3f}",  # IMP - cumulative import
                    "0.000",  # EXP - export (not available in WNSM)
                    "0.000"   # GEN-T - generation (not available in WNSM)
                ])
        
        logger.info(f"Successfully exported {len(cumulative_readings)} readings to {filepath}")
        return str(filepath)
    
    def _convert_to_cumulative(self, readings: list[EnergyReading]) -> list['CumulativeReading']:
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
    
    def export_multiple_days(self, energy_data: EnergyData) -> list[str]:
        """Export energy data split by day for better ha-backfill compatibility.
        
        Args:
            energy_data: Energy data to export
            
        Returns:
            List of paths to created CSV files
        """
        # Group readings by date
        readings_by_date: Dict[str, list[EnergyReading]] = {}
        
        for reading in energy_data.readings:
            date_key = reading.timestamp.strftime("%Y-%m-%d")
            if date_key not in readings_by_date:
                readings_by_date[date_key] = []
            readings_by_date[date_key].append(reading)
        
        exported_files = []
        cumulative_total = 0.0
        
        # Process each day in chronological order
        for date_key in sorted(readings_by_date.keys()):
            day_readings = readings_by_date[date_key]
            
            # Create daily CSV file
            filename = f"wnsm_energy_{date_key}.csv"
            filepath = self.output_dir / filename
            
            # Convert to cumulative for this day
            day_cumulative = []
            for reading in sorted(day_readings, key=lambda r: r.timestamp):
                cumulative_total += reading.value_kwh
                day_cumulative.append(
                    CumulativeReading(
                        timestamp=reading.timestamp,
                        cumulative_kwh=cumulative_total,
                        quality=reading.quality
                    )
                )
            
            # Write CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['#date', 'time', 'IMP', 'EXP', 'GEN-T'])
                
                for reading in day_cumulative:
                    date_str = reading.timestamp.strftime("%Y-%m-%d")
                    time_str = reading.timestamp.strftime("%H:%M")
                    
                    writer.writerow([
                        date_str,
                        time_str,
                        f"{reading.cumulative_kwh:.3f}",
                        "0.000",
                        "0.000"
                    ])
            
            exported_files.append(str(filepath))
            logger.info(f"Exported {len(day_cumulative)} readings to {filepath}")
        
        return exported_files
    
    def cleanup_old_files(self, days_to_keep: int = 7) -> None:
        """Clean up old CSV files.
        
        Args:
            days_to_keep: Number of days of files to keep
        """
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for file_path in self.output_dir.glob("*.csv"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    logger.debug(f"Deleted old CSV file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")


class CumulativeReading:
    """Represents a cumulative energy reading for CSV export."""
    
    def __init__(self, timestamp: datetime, cumulative_kwh: float, quality: Optional[str] = None):
        """Initialize cumulative reading.
        
        Args:
            timestamp: Reading timestamp
            cumulative_kwh: Cumulative energy consumption in kWh
            quality: Data quality indicator
        """
        self.timestamp = timestamp
        self.cumulative_kwh = cumulative_kwh
        self.quality = quality