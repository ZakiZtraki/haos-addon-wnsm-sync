# Testing Guide

This document describes how to run tests for the WNSM Sync project and what tests are available.

## Test Structure

The project uses pytest for testing with the following structure:

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_api_client.py   # API client tests (including parameter fix)
│   ├── test_config.py       # Configuration loading tests
│   ├── test_data_processor.py # Data processing tests
│   └── test_mqtt.py         # MQTT client tests
├── integration/             # Integration tests
│   └── test_sync.py         # End-to-end sync tests
└── fixtures/                # Test data and fixtures
```

## Running Tests

### Prerequisites

Make sure you have pytest installed:
```bash
pip install pytest
```

### Run All Tests

```bash
# From the wnsm-smartmeter directory
python -m pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Run only unit tests
python -m pytest tests/unit/ -v

# Run only integration tests
python -m pytest tests/integration/ -v

# Run specific test file
python -m pytest tests/unit/test_api_client.py -v
```

### Run Tests with Coverage

```bash
pip install pytest-cov
python -m pytest tests/ --cov=src/wnsm_sync --cov-report=html
```

### Using the Test Runner Script

```bash
# Run all tests
python run_tests.py

# Run specific test file
python run_tests.py unit/test_api_client.py
```

## Test Categories

### API Client Tests (`test_api_client.py`)

These tests verify the API client functionality, including:

- **Parameter Compatibility**: Tests that the `bewegungsdaten` method uses the correct parameter name (`zaehlpunktnummer` instead of `zaehlpunkt`)
- **Error Handling**: Verifies that incorrect parameter names are rejected
- **Mock Data**: Tests mock data generation and structure
- **Method Signatures**: Validates that API methods have expected signatures
- **Date Handling**: Tests different date format inputs

Key tests:
- `test_bewegungsdaten_parameter_compatibility()` - Verifies the parameter fix
- `test_bewegungsdaten_wrong_parameter_name()` - Ensures old parameter names fail
- `test_bewegungsdaten_with_retry()` - Tests retry logic integration

### Data Processor Tests (`test_data_processor.py`)

Tests for data processing logic:
- Delta value calculation for 15-minute intervals
- MQTT payload format validation
- Mock data generation

### Configuration Tests (`test_config.py`)

Tests for configuration loading:
- Environment variable parsing
- Secrets management
- Configuration validation

### MQTT Tests (`test_mqtt.py`)

Tests for MQTT functionality:
- Connection handling
- Message publishing
- Home Assistant discovery

### Integration Tests (`test_sync.py`)

End-to-end tests:
- Complete sync workflow
- Configuration loading from environment
- Mock data integration
- **Parameter fix integration test** - Verifies the bewegungsdaten fix works in the full sync flow

## The bewegungsdaten Parameter Fix

### Problem
The original code was calling the `bewegungsdaten` API method with the parameter `zaehlpunkt`, but the vienna-smartmeter library expects `zaehlpunktnummer`.

### Solution
Updated the parameter name in `src/wnsm_sync/core/sync.py`:

```python
# Before (incorrect)
raw_data = with_retry(
    self.api_client.bewegungsdaten,
    self.config,
    zaehlpunkt=self.config.zp,  # Wrong parameter name
    date_from=date_from,
    date_until=date_until
)

# After (correct)
raw_data = with_retry(
    self.api_client.bewegungsdaten,
    self.config,
    zaehlpunktnummer=self.config.zp,  # Correct parameter name
    date_from=date_from,
    date_until=date_until
)
```

### Test Coverage
The fix is covered by multiple tests:

1. **Unit Tests** (`test_api_client.py`):
   - `test_bewegungsdaten_parameter_compatibility()` - Direct API call with correct parameter
   - `test_bewegungsdaten_wrong_parameter_name()` - Verifies old parameter fails
   - `test_bewegungsdaten_method_signature()` - Validates method signature

2. **Integration Test** (`test_sync.py`):
   - `test_bewegungsdaten_parameter_fix_integration()` - End-to-end test with full sync flow

## Running Tests in CI/CD

The tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    cd wnsm-smartmeter
    python -m pytest tests/ -v --tb=short
```

## Test Data

Tests use mock data to avoid requiring real API credentials. The mock data simulates:
- 15-minute energy consumption readings
- Proper timestamp formatting
- Realistic energy values
- API response structures

## Debugging Failed Tests

If tests fail:

1. Run with verbose output: `python -m pytest tests/ -v -s`
2. Run specific failing test: `python -m pytest tests/unit/test_api_client.py::test_name -v -s`
3. Check the test output for specific error messages
4. Verify that all dependencies are installed
5. Ensure the source code structure matches the expected paths

## Adding New Tests

When adding new functionality:

1. Add unit tests for individual components
2. Add integration tests for end-to-end workflows
3. Follow the existing naming conventions (`test_*.py`)
4. Use descriptive test function names
5. Include docstrings explaining what each test verifies
6. Use appropriate assertions and error messages