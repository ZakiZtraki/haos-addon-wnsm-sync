#!/usr/bin/env python3
"""Test script for backfill functionality."""

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wnsm_sync.data.models import EnergyReading, EnergyData
from wnsm_sync.backfill.csv_exporter import CSVExporter


def test_csv_export():
    """Test CSV export functionality."""
    print("Testing CSV export...")
    
    # Create test data
    readings = []
    base_time = datetime(2024, 1, 15, 10, 0)  # Start at 10:00 AM
    
    for i in range(8):  # 8 readings = 2 hours of 15-minute intervals
        timestamp = base_time + timedelta(minutes=15 * i)
        reading = EnergyReading(
            timestamp=timestamp,
            value_kwh=0.25,  # 0.25 kWh per 15 minutes
            quality="good"
        )
        readings.append(reading)
    
    energy_data = EnergyData(
        readings=readings,
        zaehlpunkt="AT0010000000000000000000001234567890",
        date_from=base_time,
        date_until=base_time + timedelta(hours=2)
    )
    
    # Test CSV export
    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = CSVExporter(temp_dir)
        csv_file = exporter.export_energy_data(energy_data)
        
        print(f"✓ CSV file created: {csv_file}")
        
        # Read and display CSV content
        with open(csv_file, 'r') as f:
            content = f.read()
            print("CSV content:")
            print("-" * 40)
            print(content)
            print("-" * 40)
        
        # Verify CSV format
        lines = content.strip().split('\n')
        assert lines[0] == '#date,time,IMP,EXP,GEN-T', "Header format incorrect"
        assert len(lines) == 9, f"Expected 9 lines (header + 8 data), got {len(lines)}"
        
        # Check first data line
        first_data = lines[1].split(',')
        assert first_data[0] == '2024-01-15', "Date format incorrect"
        assert first_data[1] == '10:00', "Time format incorrect"
        assert first_data[2] == '0.250', "Cumulative value incorrect"
        
        # Check last data line (should be cumulative)
        last_data = lines[-1].split(',')
        assert last_data[2] == '2.000', f"Final cumulative should be 2.000, got {last_data[2]}"
        
        print("✓ CSV format validation passed")


def test_multiple_days_export():
    """Test CSV export for multiple days."""
    print("\nTesting multiple days export...")
    
    # Create test data spanning 2 days
    readings = []
    base_time = datetime(2024, 1, 15, 23, 45)  # Start near midnight
    
    for i in range(6):  # 6 readings spanning midnight
        timestamp = base_time + timedelta(minutes=15 * i)
        reading = EnergyReading(
            timestamp=timestamp,
            value_kwh=0.25,
            quality="good"
        )
        readings.append(reading)
    
    energy_data = EnergyData(
        readings=readings,
        zaehlpunkt="AT0010000000000000000000001234567890",
        date_from=base_time,
        date_until=base_time + timedelta(hours=1.5)
    )
    
    # Test multiple days export
    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = CSVExporter(temp_dir)
        csv_files = exporter.export_multiple_days(energy_data)
        
        print(f"✓ Created {len(csv_files)} CSV files")
        for csv_file in csv_files:
            print(f"  - {Path(csv_file).name}")
        
        # Should create 2 files (one for each day)
        assert len(csv_files) == 2, f"Expected 2 files, got {len(csv_files)}"
        
        print("✓ Multiple days export validation passed")


def main():
    """Run all tests."""
    print("Running backfill functionality tests...\n")
    
    try:
        test_csv_export()
        test_multiple_days_export()
        
        print("\n✓ All tests passed!")
        print("\nNext steps:")
        print("1. Install ha-backfill: python3 backfill_setup.py install")
        print("2. Test setup: python3 backfill_setup.py test")
        print("3. Run test backfill: python3 backfill_setup.py run-test")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()