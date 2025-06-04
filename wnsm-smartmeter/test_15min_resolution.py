#!/usr/bin/env python3
"""Test script to check 15-minute resolution with real credentials."""

import os
import sys
from datetime import date, timedelta

# Add src to path
sys.path.insert(0, 'src')

from wnsm_sync.api.client import Smartmeter

def test_15min_resolution():
    """Test 15-minute resolution with real credentials."""
    
    # You need to set these with your real credentials
    username = input("Enter your Wiener Netze username: ")
    password = input("Enter your Wiener Netze password: ")
    zaehlpunkt = input("Enter your Zählpunkt (or press Enter for auto-detect): ").strip()
    
    if not zaehlpunkt:
        zaehlpunkt = None  # Will auto-detect
    
    print(f"\n🔐 Testing 15-minute resolution for user: {username}")
    print("=" * 60)
    
    try:
        # Create client with OAuth
        client = Smartmeter(username, password, use_oauth=True)
        
        # Login
        print("🔑 Logging in...")
        client.login()
        print("✅ Login successful!")
        
        # Test with a short date range (last 2 days)
        date_until = date.today()
        date_from = date_until - timedelta(days=2)
        
        print(f"\n📊 Requesting data from {date_from} to {date_until}")
        print("   This will test different methods to get 15-minute data...")
        
        # Get bewegungsdaten
        bewegung = client.bewegungsdaten(
            zaehlpunktnummer=zaehlpunkt,
            date_from=date_from,
            date_until=date_until
        )
        
        data_points = bewegung.get('data', [])
        print(f"\n✅ Data retrieved successfully!")
        print(f"   Total data points: {len(data_points)}")
        
        if len(data_points) > 0:
            print(f"\n📈 First 5 data points:")
            for i, point in enumerate(data_points[:5]):
                timestamp = point.get('timestamp', 'N/A')
                value = point.get('value', 'N/A')
                print(f"   {i+1}. {timestamp} = {value} kWh")
            
            # Analyze the resolution
            expected_15min = 2 * 24 * 4  # 2 days × 24 hours × 4 intervals per hour = 192
            expected_daily = 2  # 2 days × 1 reading per day = 2
            
            print(f"\n🔍 Resolution Analysis:")
            print(f"   Expected for 15-min intervals: ~{expected_15min} points")
            print(f"   Expected for daily data: ~{expected_daily} points")
            print(f"   Actual: {len(data_points)} points")
            
            if len(data_points) >= expected_15min * 0.8:  # Allow some tolerance
                print("   🎉 SUCCESS: Getting 15-minute resolution data!")
            elif len(data_points) >= 20:  # Hourly or similar
                print("   ⚠️  Getting hourly or similar resolution (not daily)")
            else:
                print("   ❌ Still getting daily data only")
                print("   💡 Your smart meter might not support 15-minute data export")
        
        print(f"\n🎯 Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_15min_resolution()