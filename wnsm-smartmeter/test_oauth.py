#!/usr/bin/env python3
"""
Test script for OAuth authentication with vienna-smartmeter library.

Usage:
    python test_oauth.py <username> <password>

This script will test the OAuth authentication using the vienna-smartmeter library.
"""

import os
import sys
import logging
from datetime import date, timedelta

# Add src to path
sys.path.insert(0, 'src')

from wnsm_sync.api.client import Smartmeter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_oauth_authentication(username: str, password: str):
    """Test OAuth authentication with real credentials."""
    
    print(f"🔐 Testing OAuth authentication for user: {username}")
    print("=" * 60)
    
    try:
        # Create client with OAuth enabled
        client = Smartmeter(
            username=username,
            password=password,
            use_mock=False,
            api_timeout=60,
            use_oauth=True
        )
        
        print("✅ Client created successfully")
        
        # Test login
        print("\n🔑 Testing login...")
        client.login()
        print("✅ Login successful!")
        
        # Test zaehlpunkte
        print("\n📊 Testing zaehlpunkte...")
        zaehlpunkte = client.zaehlpunkte()
        print(f"✅ Found {len(zaehlpunkte)} contracts")
        
        for i, contract in enumerate(zaehlpunkte):
            print(f"   Contract {i+1}:")
            print(f"     Customer ID: {contract.get('geschaeftspartner')}")
            for j, zp in enumerate(contract.get('zaehlpunkte', [])):
                print(f"     Zaehlpunkt {j+1}: {zp.get('zaehlpunktnummer')}")
                print(f"       Type: {zp.get('anlage', {}).get('typ')}")
        
        # Test bewegungsdaten for the first zaehlpunkt
        if zaehlpunkte and zaehlpunkte[0].get('zaehlpunkte'):
            first_zp = zaehlpunkte[0]['zaehlpunkte'][0]['zaehlpunktnummer']
            print(f"\n📈 Testing bewegungsdaten for {first_zp}...")
            
            # Get data for the last 7 days
            date_until = date.today()
            date_from = date_until - timedelta(days=7)
            
            bewegungsdaten = client.bewegungsdaten(
                zaehlpunktnummer=first_zp,
                date_from=date_from,
                date_until=date_until
            )
            
            data_points = len(bewegungsdaten.get('data', []))
            print(f"✅ Retrieved {data_points} data points")
            
            if data_points > 0:
                first_point = bewegungsdaten['data'][0]
                last_point = bewegungsdaten['data'][-1]
                print(f"   First: {first_point.get('timestamp')} = {first_point.get('value')} kWh")
                print(f"   Last:  {last_point.get('timestamp')} = {last_point.get('value')} kWh")
        
        print("\n🎉 All tests passed! OAuth authentication is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    if len(sys.argv) != 3:
        print("Usage: python test_oauth.py <username> <password>")
        print("\nExample:")
        print("  python test_oauth.py your.email@example.com your_password")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    success = test_oauth_authentication(username, password)
    
    if success:
        print("\n✅ OAuth integration is working correctly!")
        print("You can now use the application with real credentials.")
    else:
        print("\n❌ OAuth integration failed.")
        print("Please check your credentials and try again.")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()