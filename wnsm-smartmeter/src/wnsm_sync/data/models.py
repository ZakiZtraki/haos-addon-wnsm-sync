"""Data models for energy readings and statistics."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal


@dataclass
class EnergyReading:
    """Represents a single 15-minute energy reading."""
    
    timestamp: datetime
    value_kwh: float
    quality: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "delta": self.value_kwh,
            "quality": self.quality
        }
    
    def to_mqtt_payload(self) -> Dict[str, Any]:
        """Convert to MQTT payload format."""
        payload = {
            "delta": self.value_kwh,
            "timestamp": self.timestamp.isoformat()
        }
        if self.quality:
            payload["quality"] = self.quality
        return payload


@dataclass
class EnergyData:
    """Collection of energy readings with metadata."""
    
    readings: List[EnergyReading]
    zaehlpunkt: str
    date_from: datetime
    date_until: datetime
    total_kwh: Optional[float] = None
    
    def __post_init__(self):
        """Calculate total if not provided."""
        if self.total_kwh is None:
            self.total_kwh = sum(reading.value_kwh for reading in self.readings)
    
    @property
    def reading_count(self) -> int:
        """Number of readings in this dataset."""
        return len(self.readings)
    
    def get_readings_for_day(self, target_date: datetime) -> List[EnergyReading]:
        """Get all readings for a specific day."""
        return [
            reading for reading in self.readings
            if reading.timestamp.date() == target_date.date()
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "zaehlpunkt": self.zaehlpunkt,
            "date_from": self.date_from.isoformat(),
            "date_until": self.date_until.isoformat(),
            "total_kwh": self.total_kwh,
            "reading_count": self.reading_count,
            "readings": [reading.to_dict() for reading in self.readings]
        }