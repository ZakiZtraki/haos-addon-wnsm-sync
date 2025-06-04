# API Timeout and Error Handling Improvements

## Issue Description
The Wiener Netze Smart Meter API was experiencing timeout issues, with requests failing after 60 seconds and returning unclear error messages like "Status: None, Error:". This made it difficult to diagnose network connectivity problems.

## Root Cause
1. **Generic error handling**: The original error handling caught all `RequestException` types generically, providing limited diagnostic information.
2. **Fixed timeout**: The API timeout was hardcoded to 60 seconds with no configuration option.
3. **Linear retry**: The retry mechanism used fixed delays, which could be inefficient for temporary network issues.

## Implemented Fixes

### 1. Enhanced Error Handling (`api/client.py`)
- **Specific Exception Handling**: Added separate handling for different types of network errors:
  - `requests.exceptions.Timeout`: Clearly identifies timeout issues
  - `requests.exceptions.ConnectionError`: Identifies network connectivity problems
  - `requests.exceptions.HTTPError`: Handles HTTP status code errors
  - `json.JSONDecodeError`: Handles malformed API responses
- **Detailed Error Messages**: Each error type now provides specific diagnostic information
- **Better Logging**: More informative error messages for troubleshooting

### 2. Configurable API Timeout (`config/loader.py`)
- **New Configuration Option**: Added `api_timeout` parameter (default: 60 seconds)
- **Environment Variable Support**: Can be configured via `API_TIMEOUT` environment variable
- **Validation**: Timeout value is properly validated and converted to integer

### 3. Improved Retry Logic (`core/utils.py`)
- **Exponential Backoff**: Retry delays now increase exponentially (10s, 20s, 40s, etc.)
- **Maximum Delay Cap**: Delays are capped at 5 minutes to prevent excessive waiting
- **Better Logging**: More informative retry messages showing current attempt and next delay

### 4. API Client Integration (`api/client.py`, `core/sync.py`)
- **Timeout Parameter**: API client now accepts and uses configurable timeout
- **Instance-level Timeout**: Each API client instance uses its configured timeout
- **Backward Compatibility**: Default timeout behavior preserved for existing code

## Configuration Options

### Environment Variables
```bash
API_TIMEOUT=30          # API request timeout in seconds (default: 60)
RETRY_COUNT=3           # Number of retry attempts (default: 3)
RETRY_DELAY=10          # Base retry delay in seconds (default: 10)
```

### Home Assistant Add-on Configuration
```json
{
  "api_timeout": 30,
  "retry_count": 3,
  "retry_delay": 10
}
```

## Error Message Examples

### Before (Generic)
```
API request failed: https://api.wstw.at/gateway/WN_SMART_METER_API/1.0/zaehlpunkte - Status: None, Error:
```

### After (Specific)
```
API request timeout: https://api.wstw.at/gateway/WN_SMART_METER_API/1.0/zaehlpunkte - Request timeout after 60 seconds
```

```
API connection error: https://api.wstw.at/gateway/WN_SMART_METER_API/1.0/zaehlpunkte - Connection error: HTTPSConnectionPool(host='api.wstw.at', port=443): Max retries exceeded
```

## Retry Behavior Examples

### Before (Linear)
```
Attempt 1/4 failed: API error. Retrying in 10 seconds...
Attempt 2/4 failed: API error. Retrying in 10 seconds...
Attempt 3/4 failed: API error. Retrying in 10 seconds...
```

### After (Exponential Backoff)
```
Attempt 1/4 failed: API timeout. Retrying in 10 seconds...
Attempt 2/4 failed: API timeout. Retrying in 20 seconds...
Attempt 3/4 failed: API timeout. Retrying in 40 seconds...
```

## Benefits

1. **Better Diagnostics**: Clear identification of timeout vs. connection vs. HTTP errors
2. **Configurable Timeouts**: Users can adjust timeout based on their network conditions
3. **Efficient Retries**: Exponential backoff reduces server load and improves success rates
4. **Improved Reliability**: Better error handling leads to more robust operation
5. **Easier Troubleshooting**: Detailed error messages help identify root causes

## Testing

The fixes have been tested with:
- ✅ Configuration loading and validation
- ✅ Timeout parameter propagation
- ✅ Mock mode functionality
- ✅ Error handling for various network conditions
- ✅ Exponential backoff retry logic

## Backward Compatibility

All changes are backward compatible:
- Default timeout values remain the same (60 seconds)
- Existing configuration files continue to work
- API interfaces are unchanged
- Mock mode continues to function as before

## Recommendations

For users experiencing timeout issues:

1. **Reduce API timeout** for faster failure detection:
   ```bash
   API_TIMEOUT=30
   ```

2. **Increase retry count** for unreliable networks:
   ```bash
   RETRY_COUNT=5
   ```

3. **Monitor logs** for specific error patterns to identify root causes

4. **Use mock mode** for testing without API calls:
   ```bash
   USE_MOCK_DATA=true
   ```