#!/usr/bin/env python3
"""
Unit tests for the API client, including parameter compatibility tests.
"""

import sys
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from wnsm_sync.api.client import Smartmeter
from wnsm_sync.api.errors import SmartmeterConnectionError, SmartmeterQueryError
from wnsm_sync.core.utils import with_retry


class MockConfig:
    """Mock configuration for retry logic."""
    retry_count = 3
    retry_delay = 1


def test_bewegungsdaten_parameter_compatibility():
    """Test that bewegungsdaten method uses the correct parameter name."""
    # Create a mock client
    client = Smartmeter('test_user', 'test_pass', use_mock=True)
    
    # Test dates
    date_until = datetime.now()
    date_from = date_until - timedelta(days=1)
    
    # Test the method call with the correct parameter name
    result = client.bewegungsdaten(
        zaehlpunktnummer="AT0010000000000000000000000000000",
        date_from=date_from,
        date_until=date_until
    )
    
    # Should return mock data successfully
    assert result is not None
    assert isinstance(result, dict)
    assert "data" in result or "values" in result  # Different formats possible
    
    print("✓ Successfully called bewegungsdaten with zaehlpunktnummer parameter")


def test_bewegungsdaten_wrong_parameter_name():
    """Test that bewegungsdaten method rejects the old parameter name."""
    client = Smartmeter('test_user', 'test_pass', use_mock=True)
    
    date_until = datetime.now()
    date_from = date_until - timedelta(days=1)
    
    # Test that the old parameter name fails
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        client.bewegungsdaten(
            zaehlpunkt="AT0010000000000000000000000000000",  # Wrong parameter name
            date_from=date_from,
            date_until=date_until
        )
    
    print("✓ Correctly rejected old parameter name 'zaehlpunkt'")


def test_bewegungsdaten_with_retry():
    """Test bewegungsdaten method with retry logic."""
    client = Smartmeter('test_user', 'test_pass', use_mock=True)
    config = MockConfig()
    
    date_until = datetime.now()
    date_from = date_until - timedelta(days=1)
    
    # This should work with the retry wrapper
    result = with_retry(
        client.bewegungsdaten,
        config,
        zaehlpunktnummer="AT0010000000000000000000000000000",
        date_from=date_from,
        date_until=date_until
    )
    
    assert result is not None
    assert isinstance(result, dict)
    
    print("✓ Successfully called bewegungsdaten with retry wrapper")


def test_bewegungsdaten_mock_data_structure():
    """Test that mock bewegungsdaten returns expected data structure."""
    client = Smartmeter('test_user', 'test_pass', use_mock=True)
    
    date_until = datetime.now()
    date_from = date_until - timedelta(days=1)
    
    result = client.bewegungsdaten(
        zaehlpunktnummer="AT0010000000000000000000000000000",
        date_from=date_from,
        date_until=date_until
    )
    
    # Check the structure of mock data
    assert result is not None
    assert isinstance(result, dict)
    
    # Mock data should have either 'data' or 'values' key
    has_data = "data" in result
    has_values = "values" in result
    assert has_data or has_values, "Mock data should have 'data' or 'values' key"
    
    if has_data:
        assert isinstance(result["data"], list)
        print(f"✓ Mock data contains {len(result['data'])} data points")
    
    if has_values:
        assert isinstance(result["values"], list)
        print(f"✓ Mock data contains {len(result['values'])} value points")


def test_smartmeter_initialization():
    """Test Smartmeter client initialization."""
    # Test with mock mode
    client = Smartmeter('test_user', 'test_pass', use_mock=True)
    assert client is not None
    
    # Test without mock mode
    client_real = Smartmeter('test_user', 'test_pass', use_mock=False)
    assert client_real is not None
    
    print("✓ Smartmeter client initialization works correctly")


def test_smartmeter_reset():
    """Test Smartmeter client reset functionality."""
    client = Smartmeter('test_user', 'test_pass', use_mock=True)
    
    # Reset should not raise any errors
    client.reset()
    
    print("✓ Smartmeter client reset works correctly")


def test_bewegungsdaten_method_signature():
    """Test that bewegungsdaten method has the expected signature."""
    import inspect
    
    client = Smartmeter('test_user', 'test_pass', use_mock=True)
    method = getattr(client, 'bewegungsdaten')
    sig = inspect.signature(method)
    
    # Check that the first parameter is 'zaehlpunktnummer'
    params = list(sig.parameters.keys())
    assert 'zaehlpunktnummer' in params, "Method should have 'zaehlpunktnummer' parameter"
    assert 'zaehlpunkt' not in params, "Method should not have old 'zaehlpunkt' parameter"
    
    # Check other expected parameters
    expected_params = ['zaehlpunktnummer', 'date_from', 'date_until', 'valuetype', 'aggregat']
    for param in expected_params:
        assert param in params, f"Method should have '{param}' parameter"
    
    print("✓ bewegungsdaten method signature is correct")


def test_bewegungsdaten_default_parameters():
    """Test bewegungsdaten method with default parameters."""
    client = Smartmeter('test_user', 'test_pass', use_mock=True)
    
    # Should work with minimal parameters
    result = client.bewegungsdaten()
    
    assert result is not None
    assert isinstance(result, dict)
    
    print("✓ bewegungsdaten works with default parameters")


def test_bewegungsdaten_date_handling():
    """Test bewegungsdaten method with different date formats."""
    client = Smartmeter('test_user', 'test_pass', use_mock=True)
    
    # Test with datetime objects
    date_until = datetime.now()
    date_from = date_until - timedelta(days=1)
    
    result = client.bewegungsdaten(
        zaehlpunktnummer="AT0010000000000000000000000000000",
        date_from=date_from,
        date_until=date_until
    )
    
    assert result is not None
    
    # Test with date objects
    from datetime import date
    date_until_date = date.today()
    date_from_date = date_until_date - timedelta(days=1)
    
    result2 = client.bewegungsdaten(
        zaehlpunktnummer="AT0010000000000000000000000000000",
        date_from=date_from_date,
        date_until=date_until_date
    )
    
    assert result2 is not None
    
    print("✓ bewegungsdaten handles different date formats correctly")


if __name__ == "__main__":
    print("Testing API client...")
    print("=" * 50)
    
    # Run all tests
    test_bewegungsdaten_parameter_compatibility()
    test_bewegungsdaten_wrong_parameter_name()
    test_bewegungsdaten_with_retry()
    test_bewegungsdaten_mock_data_structure()
    test_smartmeter_initialization()
    test_smartmeter_reset()
    test_bewegungsdaten_method_signature()
    test_bewegungsdaten_default_parameters()
    test_bewegungsdaten_date_handling()
    
    print("=" * 50)
    print("🎉 All API client tests passed!")