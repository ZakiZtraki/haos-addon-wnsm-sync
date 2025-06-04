# Fix for Wiener Netze API Authentication Issues

## Problem
Since May 22, 2025, the Wiener Netze Smart Meter API has changed its authentication method, causing 401 Unauthorized errors with the current vienna-smartmeter library.

## Root Cause
The API now requires PKCE (Proof Key for Code Exchange) for OAuth authentication, which the current vienna-smartmeter library doesn't support.

## Solution

### Option 1: Install Fixed Version (Recommended)

Install the fixed version directly from the GitHub pull request:

```bash
# Uninstall current version
pip uninstall vienna-smartmeter

# Install fixed version from GitHub
pip install git+https://github.com/cretl/vienna-smartmeter.git@fix-login-add-pkce
```

### Option 2: Update requirements.txt

Update your `requirements.txt` file:

```txt
# Replace this line:
# vienna-smartmeter==0.3.2

# With this:
git+https://github.com/cretl/vienna-smartmeter.git@fix-login-add-pkce
```

### Option 3: Wait for Official Release

The fix is available in Pull Request #182 on the main repository. Once merged and released, you can update normally:

```bash
pip install --upgrade vienna-smartmeter
```

## What the Fix Includes

1. **PKCE Support**: Adds Proof Key for Code Exchange to the OAuth flow
2. **Updated Login Flow**: Handles the new authentication requirements
3. **API Endpoint Updates**: Includes other recent API changes
4. **Bewegungsdaten Support**: Enhanced support for energy data retrieval

## Testing the Fix

After installing the fixed version, test with:

```python
from vienna_smartmeter import Smartmeter

# This should now work without 401 errors
api = Smartmeter('your_username', 'your_password')
print("Login successful!")
```

## For Home Assistant Add-on

If you're using this in a Home Assistant add-on, update your Dockerfile:

```dockerfile
# Replace vienna-smartmeter installation with:
RUN pip install git+https://github.com/cretl/vienna-smartmeter.git@fix-login-add-pkce
```

## Status

- ✅ **Fix Available**: Working solution exists
- ⏳ **Pending Merge**: Waiting for maintainer to merge PR #182
- 🧪 **Tested**: Confirmed working by multiple users
- 📅 **Timeline**: Fix available since May 29, 2025

## References

- [GitHub Issue #181](https://github.com/platysma/vienna-smartmeter/issues/181)
- [GitHub Pull Request #182](https://github.com/platysma/vienna-smartmeter/pull/182)
- [Original Fix by cretl](https://github.com/cretl/vienna-smartmeter/tree/fix-login-add-pkce)