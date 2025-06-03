#!/usr/bin/env python3
"""
Test script to verify the delta fix for 15-minute intervals.
This script tests the main processing logic without requiring actual API calls.
"""

import sys
import os
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from wnsm_sync.data.processor import DataProcessor
from wnsm_sync.data.models import EnergyReading, EnergyData

def test_delta_processing():
    """Test that the data processor creates correct delta values."""
    
    # Mock bewegungsdaten response (similar to what the API returns)
    mock_bewegungsdaten = {
        "values": [
            {
                "zeitpunkt": "2025-01-15T00:15:00Z",
                "wert": "0.234"  # 15-minute consumption in kWh
            },
            {
                "zeitpunkt": "2025-01-15T00:30:00Z", 
                "wert": "0.187"  # 15-minute consumption in kWh
            },
            {
                "zeitpunkt": "2025-01-15T00:45:00Z",
                "wert": "0.156"  # 15-minute consumption in kWh
            }
        ]
    }
    
    # Create data processor
    processor = DataProcessor()
    
    # Process the data
    energy_data = processor.process_bewegungsdaten_response(
        mock_bewegungsdaten, 
        "AT0010000000000000001000004392265"
    )
    
    # Verify results
    assert energy_data is not None
    assert len(energy_data.readings) == 3
    
    # Check individual readings
    expected_values = [0.234, 0.187, 0.156]
    for i, reading in enumerate(energy_data.readings):
        assert reading.value_kwh == expected_values[i]
        assert isinstance(reading.timestamp, datetime)
    
    # Check total
    assert energy_data.total_kwh == sum(expected_values)
    
    print(f"✅ Processed {len(energy_data.readings)} readings correctly")
    print(f"✅ Total consumption: {energy_data.total_kwh} kWh")


def test_mqtt_payload_format():
    """Test that MQTT payloads are in the correct format."""
    
    # Create a sample reading
    reading = EnergyReading(
        timestamp=datetime(2025, 1, 15, 0, 15),
        value_kwh=0.234
    )
    
    # Test MQTT payload format
    payload = reading.to_mqtt_payload()
    
    # Verify payload structure
    assert "delta" in payload, "Payload must contain 'delta' field"
    assert "timestamp" in payload, "Payload must contain 'timestamp' field"
    assert payload["delta"] == 0.234, "Delta value must match"
    assert isinstance(payload["timestamp"], str), "Timestamp must be a string"
    
    print("✅ MQTT payload format is correct!")


def test_mock_data_generation():
    """Test mock data generation."""
    
    processor = DataProcessor()
    
    date_from = datetime(2025, 1, 15, 0, 0)
    date_until = datetime(2025, 1, 15, 1, 0)  # 1 hour = 4 intervals
    
    energy_data = processor.generate_mock_data(
        date_from=date_from,
        date_until=date_until,
        zaehlpunkt="AT0010000000000000001000004392265"
    )
    
    # Should have 4 readings (15-minute intervals in 1 hour)
    assert len(energy_data.readings) == 4
    assert energy_data.zaehlpunkt == "AT0010000000000000001000004392265"
    
    # All readings should have positive values
    for reading in energy_data.readings:
        assert reading.value_kwh > 0
        assert reading.quality == "mock"
    
    print("✅ Mock data generation works correctly!")


if __name__ == "__main__":
    print("Testing the data processor...")
    
    # Run all tests
    test_delta_processing()
    test_mqtt_payload_format()
    test_mock_data_generation()
    
    print("\n🎉 All tests passed!")