#!/usr/bin/env python3
"""Detailed test script to debug 15-minute resolution issues."""

import os
import sys
import logging
from datetime import date, timedelta

# Add src to path
sys.path.insert(0, 'src')

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from wnsm_sync.api.client import Smartmeter

def test_all_resolution_methods():
    """Test all possible methods to get high-resolution data."""
    
    # You need to set these with your real credentials
    username = input("Enter your Wiener Netze username: ")
    password = input("Enter your Wiener Netze password: ")
    zaehlpunkt = input("Enter your Zählpunkt (or press Enter for auto-detect): ").strip()
    
    if not zaehlpunkt:
        zaehlpunkt = None  # Will auto-detect
    
    print(f"\n🔐 Detailed resolution testing for user: {username}")
    print("=" * 70)
    
    try:
        # Create client with OAuth
        client = Smartmeter(username, password, use_oauth=True)
        
        # Login
        print("🔑 Logging in...")
        client.login()
        print("✅ Login successful!")
        
        # Get zaehlpunkt info
        if not zaehlpunkt:
            customer_id, zaehlpunkt, anlagetype = client.get_zaehlpunkt()
            print(f"📍 Auto-detected Zählpunkt: {zaehlpunkt}")
            print(f"   Customer ID: {customer_id}")
            print(f"   Anlage Type: {anlagetype}")
        
        # Test with a very short date range (just yesterday)
        date_until = date.today()
        date_from = date_until - timedelta(days=1)
        
        print(f"\n📊 Testing with date range: {date_from} to {date_until}")
        print("   (1 day should give us ~96 points for 15-min intervals)")
        
        # Test 1: Direct vienna-smartmeter library calls
        print(f"\n🧪 Test 1: Direct bewegungsdaten calls")
        print("-" * 50)
        
        # Test different rolle values
        for rolle in ["V001", "V002", None]:
            try:
                print(f"\n   Testing rolle='{rolle}'...")
                data = client._client.bewegungsdaten(
                    zaehlpunkt=zaehlpunkt,
                    date_from=date_from,
                    date_to=date_until,
                    rolle=rolle
                )
                values = data.get('values', [])
                print(f"   ✅ rolle='{rolle}': {len(values)} data points")
                
                if values:
                    first_point = values[0]
                    print(f"      First point: {first_point}")
                    
                    # Check time span of first point
                    zeit_von = first_point.get('zeitpunktVon', '')
                    zeit_bis = first_point.get('zeitpunktBis', '')
                    print(f"      Time span: {zeit_von} to {zeit_bis}")
                    
            except Exception as e:
                print(f"   ❌ rolle='{rolle}': Error - {e}")
        
        # Test 2: Different aggregat values
        print(f"\n🧪 Test 2: Different aggregat values with rolle=V001")
        print("-" * 50)
        
        for aggregat in [None, "NONE", "SUM_PER_DAY"]:
            try:
                print(f"\n   Testing aggregat='{aggregat}'...")
                data = client._client.bewegungsdaten(
                    zaehlpunkt=zaehlpunkt,
                    date_from=date_from,
                    date_to=date_until,
                    rolle="V001",
                    aggregat=aggregat
                )
                values = data.get('values', [])
                print(f"   ✅ aggregat='{aggregat}': {len(values)} data points")
                
            except Exception as e:
                print(f"   ❌ aggregat='{aggregat}': Error - {e}")
        
        # Test 3: messwerte method
        print(f"\n🧪 Test 3: messwerte method")
        print("-" * 50)
        
        try:
            print(f"\n   Testing messwerte...")
            data = client._client.messwerte(
                zaehlpunkt=zaehlpunkt,
                date_from=date_from,
                date_to=date_until,
                wertetyp='METER_READ'
            )
            values = data.get('values', [])
            print(f"   ✅ messwerte: {len(values)} data points")
            
            if values:
                first_point = values[0]
                print(f"      First point: {first_point}")
                
        except Exception as e:
            print(f"   ❌ messwerte: Error - {e}")
        
        # Test 4: Check available methods
        print(f"\n🧪 Test 4: Available data methods")
        print("-" * 50)
        
        methods_to_test = ['verbrauch', 'verbrauch_raw', 'consumptions', 'meterReadings']
        
        for method_name in methods_to_test:
            if hasattr(client._client, method_name):
                try:
                    print(f"\n   Testing {method_name}...")
                    method = getattr(client._client, method_name)
                    
                    # Try to call with minimal parameters
                    if method_name in ['verbrauch', 'verbrauch_raw']:
                        data = method(date_from, date_until, zaehlpunkt)
                    else:
                        data = method()
                    
                    if isinstance(data, dict):
                        values = data.get('values', data.get('data', []))
                        print(f"   ✅ {method_name}: {len(values) if isinstance(values, list) else 'dict'} items")
                    elif isinstance(data, list):
                        print(f"   ✅ {method_name}: {len(data)} items")
                    else:
                        print(f"   ✅ {method_name}: {type(data)} returned")
                        
                except Exception as e:
                    print(f"   ❌ {method_name}: Error - {e}")
        
        print(f"\n🎯 Detailed testing completed!")
        print(f"\n💡 Summary:")
        print(f"   If all methods return only 1-2 data points per day,")
        print(f"   your smart meter likely doesn't support 15-minute data export.")
        print(f"   This is common with older smart meters or certain configurations.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_all_resolution_methods()