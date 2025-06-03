"""Data processing logic for energy readings."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

from .models import EnergyReading, EnergyData

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes raw API data into structured energy readings."""
    
    def __init__(self):
        """Initialize data processor."""
        pass
    
    def process_bewegungsdaten_response(
        self, 
        raw_data: Dict[str, Any], 
        zaehlpunkt: str
    ) -> Optional[EnergyData]:
        """Process raw bewegungsdaten API response into structured data.
        
        Args:
            raw_data: Raw response from the bewegungsdaten API
            zaehlpunkt: The meter point identifier
            
        Returns:
            EnergyData object with processed readings, or None if processing fails
        """
        try:
            if not raw_data or "values" not in raw_data:
                logger.warning("No values found in bewegungsdaten response")
                return None
            
            readings = []
            values = raw_data["values"]
            
            logger.info(f"Processing {len(values)} raw data points")
            
            for entry in values:
                try:
                    reading = self._process_single_entry(entry)
                    if reading:
                        readings.append(reading)
                except Exception as e:
                    logger.warning(f"Failed to process entry {entry}: {e}")
                    continue
            
            if not readings:
                logger.warning("No valid readings processed")
                return None
            
            # Determine date range from readings
            timestamps = [r.timestamp for r in readings]
            date_from = min(timestamps)
            date_until = max(timestamps)
            
            energy_data = EnergyData(
                readings=readings,
                zaehlpunkt=zaehlpunkt,
                date_from=date_from,
                date_until=date_until
            )
            
            logger.info(
                f"Processed {len(readings)} readings from {date_from.date()} "
                f"to {date_until.date()}, total: {energy_data.total_kwh:.3f} kWh"
            )
            
            return energy_data
            
        except Exception as e:
            logger.error(f"Failed to process bewegungsdaten response: {e}")
            return None
    
    def _process_single_entry(self, entry: Dict[str, Any]) -> Optional[EnergyReading]:
        """Process a single data entry into an EnergyReading.
        
        Args:
            entry: Single entry from the API response
            
        Returns:
            EnergyReading object or None if processing fails
        """
        try:
            # Extract timestamp
            if "zeitpunkt" in entry:
                timestamp_str = entry["zeitpunkt"]
                timestamp = self._parse_timestamp(timestamp_str)
            else:
                logger.warning(f"No timestamp found in entry: {entry}")
                return None
            
            # Extract value
            if "wert" in entry:
                value_kwh = float(entry["wert"])
            else:
                logger.warning(f"No value found in entry: {entry}")
                return None
            
            # Extract quality if available
            quality = entry.get("qualitaet")
            
            return EnergyReading(
                timestamp=timestamp,
                value_kwh=value_kwh,
                quality=quality
            )
            
        except Exception as e:
            logger.warning(f"Failed to process entry {entry}: {e}")
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string into datetime object.
        
        Args:
            timestamp_str: Timestamp string from API
            
        Returns:
            Parsed datetime object
        """
        # Try different timestamp formats
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",      # ISO format with timezone
            "%Y-%m-%dT%H:%M:%S",        # ISO format without timezone
            "%Y-%m-%d %H:%M:%S",        # Space-separated format
            "%d.%m.%Y %H:%M:%S",        # German format
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # If all formats fail, try parsing with fromisoformat
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        raise ValueError(f"Unable to parse timestamp: {timestamp_str}")
    
    def generate_mock_data(
        self, 
        date_from: datetime, 
        date_until: datetime,
        zaehlpunkt: str
    ) -> EnergyData:
        """Generate mock energy data for testing.
        
        Args:
            date_from: Start date for mock data
            date_until: End date for mock data
            zaehlpunkt: Meter point identifier
            
        Returns:
            EnergyData with mock readings
        """
        import random
        
        readings = []
        current_time = date_from
        
        logger.info(f"Generating mock data from {date_from} to {date_until}")
        
        while current_time < date_until:
            # Generate realistic 15-minute consumption (0.1 to 0.8 kWh)
            base_consumption = 0.2  # Base consumption
            variation = random.uniform(-0.1, 0.3)  # Random variation
            value_kwh = max(0.05, base_consumption + variation)  # Ensure positive
            
            reading = EnergyReading(
                timestamp=current_time,
                value_kwh=round(value_kwh, 3),
                quality="mock"
            )
            readings.append(reading)
            
            # Move to next 15-minute interval
            current_time += timedelta(minutes=15)
        
        energy_data = EnergyData(
            readings=readings,
            zaehlpunkt=zaehlpunkt,
            date_from=date_from,
            date_until=date_until
        )
        
        logger.info(f"Generated {len(readings)} mock readings, total: {energy_data.total_kwh:.3f} kWh")
        
        return energy_data