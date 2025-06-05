#!/usr/bin/env python3
"""Test script to verify timezone handling fix."""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wnsm_sync.backfill.python_backfill import normalize_timestamp_to_utc


def test_timezone_normalization():
    """Test the timezone normalization function."""
    print("Testing timezone normalization...")
    
    # Test timezone-naive datetime (should pass through unchanged)
    naive_dt = datetime(2025, 6, 4, 21, 30, 0)
    normalized_naive = normalize_timestamp_to_utc(naive_dt)
    print(f"Naive datetime: {naive_dt} -> {normalized_naive}")
    assert normalized_naive == naive_dt
    assert normalized_naive.tzinfo is None
    
    # Test timezone-aware datetime (should convert to UTC and remove timezone)
    aware_dt = datetime(2025, 6, 4, 21, 30, 0, tzinfo=timezone.utc)
    normalized_aware = normalize_timestamp_to_utc(aware_dt)
    print(f"Aware datetime: {aware_dt} -> {normalized_aware}")
    assert normalized_aware.tzinfo is None
    assert normalized_aware == datetime(2025, 6, 4, 21, 30, 0)
    
    # Test timezone-aware datetime with offset
    offset_tz = timezone(timedelta(hours=2))  # +02:00
    offset_dt = datetime(2025, 6, 4, 23, 30, 0, tzinfo=offset_tz)  # 23:30 +02:00 = 21:30 UTC
    normalized_offset = normalize_timestamp_to_utc(offset_dt)
    print(f"Offset datetime: {offset_dt} -> {normalized_offset}")
    assert normalized_offset.tzinfo is None
    assert normalized_offset == datetime(2025, 6, 4, 21, 30, 0)  # Should be 21:30 UTC
    
    # Test comparison between normalized timestamps
    timestamps = [naive_dt, aware_dt, offset_dt]
    normalized = [normalize_timestamp_to_utc(ts) for ts in timestamps]
    
    print(f"Original timestamps: {timestamps}")
    print(f"Normalized timestamps: {normalized}")
    
    # This should not raise an exception anymore
    try:
        min_time = min(normalized)
        max_time = max(normalized)
        print(f"Min time: {min_time}")
        print(f"Max time: {max_time}")
        print("✅ Comparison successful - no timezone errors!")
    except TypeError as e:
        print(f"❌ Comparison failed: {e}")
        return False
    
    return True


def main():
    """Main test function."""
    print("="*60)
    print("TIMEZONE HANDLING FIX TEST")
    print("="*60)
    
    success = test_timezone_normalization()
    
    if success:
        print("\n✅ All tests passed!")
        print("The timezone handling fix should resolve the backfill error.")
        print("\nNext steps:")
        print("1. Restart your add-on to apply the fix")
        print("2. Check the logs for successful backfill operations")
        print("3. Verify that historical data appears with correct timestamps in Home Assistant")
    else:
        print("\n❌ Tests failed!")
        print("There may be additional issues to resolve.")


if __name__ == "__main__":
    main()