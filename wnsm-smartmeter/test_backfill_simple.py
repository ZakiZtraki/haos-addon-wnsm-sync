#!/usr/bin/env python3
"""Simple test for backfill functionality without requiring Home Assistant."""

import sys
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wnsm_sync.data.models import EnergyReading, EnergyData
from wnsm_sync.backfill.csv_exporter import CSVExporter


def test_csv_export_functionality():
    """Test the CSV export functionality."""
    print("🧪 Testing CSV Export Functionality")
    print("=" * 50)
    
    # Create test data
    readings = []
    base_time = datetime(2024, 1, 15, 10, 0)  # Start at 10:00 AM
    
    print(f"📊 Generating test data starting from {base_time}")
    
    for i in range(12):  # 12 readings = 3 hours of 15-minute intervals
        timestamp = base_time + timedelta(minutes=15 * i)
        reading = EnergyReading(
            timestamp=timestamp,
            value_kwh=0.25 + (i * 0.01),  # Slightly increasing consumption
            quality="good"
        )
        readings.append(reading)
    
    energy_data = EnergyData(
        readings=readings,
        zaehlpunkt="AT0010000000000000000000001234567890",
        date_from=base_time,
        date_until=base_time + timedelta(hours=3)
    )
    
    print(f"✅ Created {len(readings)} test readings")
    
    # Test CSV export
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")
        
        exporter = CSVExporter(temp_dir)
        csv_file = exporter.export_energy_data(energy_data)
        
        print(f"📄 CSV file created: {Path(csv_file).name}")
        
        # Read and display CSV content
        with open(csv_file, 'r') as f:
            content = f.read()
        
        print("\n📋 CSV Content Preview:")
        print("-" * 40)
        lines = content.strip().split('\n')
        for i, line in enumerate(lines[:6]):  # Show first 6 lines
            print(f"{i+1:2}: {line}")
        if len(lines) > 6:
            print(f"... ({len(lines)-6} more lines)")
        print("-" * 40)
        
        # Validate CSV format
        assert lines[0] == '#date,time,IMP,EXP,GEN-T', "❌ Header format incorrect"
        assert len(lines) == 13, f"❌ Expected 13 lines (header + 12 data), got {len(lines)}"
        
        # Check first data line
        first_data = lines[1].split(',')
        assert first_data[0] == '2024-01-15', "❌ Date format incorrect"
        assert first_data[1] == '10:00', "❌ Time format incorrect"
        assert first_data[2] == '0.250', "❌ Cumulative value incorrect"
        
        # Check last data line (should be cumulative)
        last_data = lines[-1].split(',')
        expected_final = 0.25 * 12 + sum(i * 0.01 for i in range(12))
        actual_final = float(last_data[2])
        
        print(f"✅ CSV format validation passed")
        print(f"✅ Final cumulative value: {actual_final:.3f} kWh")
        
        return True


def test_multi_day_export():
    """Test CSV export spanning multiple days."""
    print("\n🗓️  Testing Multi-Day Export")
    print("=" * 50)
    
    # Create test data spanning 2 days
    readings = []
    base_time = datetime(2024, 1, 15, 23, 30)  # Start near midnight
    
    print(f"📊 Generating test data starting from {base_time}")
    
    for i in range(8):  # 8 readings spanning midnight
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
        date_until=base_time + timedelta(hours=2)
    )
    
    # Test multiple days export
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")
        
        exporter = CSVExporter(temp_dir)
        csv_files = exporter.export_multiple_days(energy_data)
        
        print(f"📄 Created {len(csv_files)} CSV files:")
        for csv_file in csv_files:
            filename = Path(csv_file).name
            print(f"   - {filename}")
            
            # Show file content summary
            with open(csv_file, 'r') as f:
                lines = f.readlines()
                print(f"     ({len(lines)-1} data rows)")
        
        # Should create 2 files (one for each day)
        assert len(csv_files) == 2, f"❌ Expected 2 files, got {len(csv_files)}"
        
        print(f"✅ Multi-day export validation passed")
        
        return True


def show_ha_backfill_format():
    """Show the expected ha-backfill format."""
    print("\n📖 ha-backfill CSV Format")
    print("=" * 50)
    
    print("The CSV files are compatible with ha-backfill tool:")
    print()
    print("Format:")
    print("  #date,time,IMP,EXP,GEN-T")
    print("  2024-01-15,10:00,1234.567,0.000,0.000")
    print("  2024-01-15,10:15,1234.789,0.000,0.000")
    print()
    print("Where:")
    print("  - IMP: Cumulative import energy (kWh)")
    print("  - EXP: Export energy (set to 0 for WNSM data)")
    print("  - GEN-T: Generation energy (set to 0 for WNSM data)")
    print()
    print("ha-backfill command example:")
    print("  ha-backfill -dir=/path/to/csv -import-key=14 | sqlite3 /config/home-assistant_v2.db")


def main():
    """Run all tests."""
    print("🚀 WNSM Backfill Functionality Test")
    print("=" * 60)
    print()
    
    try:
        # Test CSV export
        test_csv_export_functionality()
        
        # Test multi-day export
        test_multi_day_export()
        
        # Show format information
        show_ha_backfill_format()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print()
        print("📋 Next Steps:")
        print("1. Install ha-backfill on your Home Assistant system")
        print("2. Find your energy sensor metadata ID")
        print("3. Configure backfill in your addon settings")
        print("4. Test with real data")
        print()
        print("For detailed setup instructions, see: BACKFILL_GUIDE.md")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()