#!/usr/bin/env python3
"""Test script using environment variables."""

import os
import sys
from datetime import date, timedelta

# Set your credentials here
os.environ.update({
    'WNSM_USERNAME': 'biryukov.vladimir.anatol@gmail.com',  # Replace with your username
    'WNSM_PASSWORD': 'YOUR_ACTUAL_PASSWORD',  # Replace with your password
    'WNSM_ZP': 'AT0010000000000000001000004392265',  # Replace with your Zählpunkt
    'MQTT_HOST': 'localhost',
    'USE_OAUTH': 'true',
    'USE_MOCK_DATA': 'false'  # Use real data
})

# Add src to path
sys.path.insert(0, 'src')

from wnsm_sync.api.client import Smartmeter
from wnsm_sync.data.processor import DataProcessor

def test_real_15min_data():
    """Test 15-minute resolution with real data."""
    
    username = os.environ['WNSM_USERNAME']
    password = os.environ['WNSM_PASSWORD']
    zaehlpunkt = os.environ['WNSM_ZP']
    
    print(f"🔐 Testing 15-minute resolution for user: {username}")
    print("=" * 60)
    
    try:
        # Create client and processor
        client = Smartmeter(username, password, use_oauth=True)
        processor = DataProcessor()
        
        # Login
        print("🔑 Logging in...")
        client.login()
        print("✅ Login successful!")
        
        # Test with last 2 days
        date_until = date.today()
        date_from = date_until - timedelta(days=2)
        
        print(f"\n📊 Requesting data from {date_from} to {date_until}")
        
        # Get bewegungsdaten
        bewegung = client.bewegungsdaten(
            zaehlpunktnummer=zaehlpunkt,
            date_from=date_from,
            date_until=date_until
        )
        
        print(f"✅ Raw data retrieved: {len(bewegung.get('data', []))} points")
        
        # Process data
        energy_data = processor.process_bewegungsdaten_response(bewegung, zaehlpunkt)
        
        if energy_data:
            print(f"✅ Data processing successful!")
            print(f"   Processed readings: {len(energy_data.readings)}")
            print(f"   Total kWh: {energy_data.total_kwh}")
            
            if energy_data.readings:
                print(f"\n📈 First 5 readings:")
                for i, reading in enumerate(energy_data.readings[:5]):
                    print(f"   {i+1}. {reading.timestamp} = {reading.value_kwh} kWh")
                
                # Check resolution
                expected_15min = 2 * 24 * 4  # 192 points for 2 days
                actual = len(energy_data.readings)
                
                print(f"\n🔍 Resolution Analysis:")
                print(f"   Expected for 15-min: ~{expected_15min} readings")
                print(f"   Actual: {actual} readings")
                
                if actual >= expected_15min * 0.8:
                    print("   🎉 SUCCESS: 15-minute resolution!")
                elif actual >= 20:
                    print("   ⚠️  Hourly or similar resolution")
                else:
                    print("   ❌ Daily resolution only")
        
        print(f"\n🎯 Complete test finished!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_15min_data()