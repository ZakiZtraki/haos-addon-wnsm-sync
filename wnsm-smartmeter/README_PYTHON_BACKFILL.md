# 🐍 Python Backfill - Home Assistant OS Compatible Solution

## 🎯 Perfect for Home Assistant OS!

Since Home Assistant OS doesn't allow permanent installation of external binaries like `ha-backfill`, we've created a **pure Python implementation** that works perfectly within the addon environment.

## ✨ Key Advantages

- ✅ **No external dependencies** - Pure Python, no Go compilation needed
- ✅ **Home Assistant OS compatible** - Works in the restricted addon environment
- ✅ **Same functionality** - Direct database insertion with correct timestamps
- ✅ **Automatic by default** - Enabled automatically, no manual setup required
- ✅ **Safer** - No need to stop Home Assistant during operation

## 🚀 Quick Test

Test the Python backfill functionality right now:

```bash
# Test CSV export (works anywhere)
python test_backfill_simple.py

# Test Python backfill setup
python backfill_setup.py test --config test_config.json
```

## ⚙️ Configuration

Simply add these to your WNSM addon configuration:

```yaml
# Enable backfill for historical data
ENABLE_BACKFILL: true

# Use Python implementation (default, recommended for Home Assistant OS)
USE_PYTHON_BACKFILL: true

# Your energy sensor's metadata ID (find this using the diagnostic script)
HA_IMPORT_METADATA_ID: "14"
```

## 🔍 Find Your Sensor Metadata ID

Run this on your Home Assistant system to find your energy sensor ID:

```bash
python backfill_setup.py test
```

Look for output like:
```
Available energy sensors in Home Assistant:
  ID:  14 | sensor.energy_consumption_kwh
  ID:  15 | sensor.energy_production_kwh
```

Use the ID number for your consumption sensor.

## 🔄 How It Works

### Automatic Mode Selection
```
📊 Energy Data from WNSM API
    ↓
🤖 Smart Detection
    ↓
📡 Recent data (< 24h) → MQTT → Real-time updates
💾 Historical data (> 24h) → Python Backfill → Correct timestamps
    ↓
🏠 Home Assistant Energy Dashboard
```

### Python Backfill Process
1. **Convert to Cumulative** - Transform 15-minute delta readings to cumulative values
2. **Database Connection** - Connect directly to Home Assistant SQLite database
3. **Clean Insert** - Remove existing data in time range, insert new with correct timestamps
4. **Statistics Tables** - Updates both long-term and short-term statistics tables

## 📊 Database Integration

The Python implementation directly inserts into Home Assistant's statistics tables:

- **`statistics`** - Long-term data (hourly records)
- **`statistics_short_term`** - Short-term data (5-minute records, last 14 days)

This ensures perfect integration with:
- Energy Dashboard
- History graphs
- Statistics sensors
- Long-term energy tracking

## 🧪 Testing

### Test CSV Export (Safe, works anywhere)
```bash
python test_backfill_simple.py
```

### Test Python Backfill Setup
```bash
python backfill_setup.py test --config test_config.json
```

### Test with Mock Data (Safe, no real database changes)
```bash
python backfill_setup.py run-test --config test_config.json
```

## 🔧 Advanced Configuration

```yaml
# Basic settings
ENABLE_BACKFILL: true
USE_PYTHON_BACKFILL: true
HA_IMPORT_METADATA_ID: "14"

# Advanced settings (optional)
HA_DATABASE_PATH: "/config/home-assistant_v2.db"  # Default path
HA_SHORT_TERM_DAYS: 14  # Days to keep short-term statistics

# If you want to use external ha-backfill instead (not recommended for HA OS)
USE_PYTHON_BACKFILL: false
HA_BACKFILL_BINARY: "/usr/local/bin/ha-backfill"
```

## 📈 Results

### Before (MQTT Only)
```
❌ Historical data clustered at current time
Energy Dashboard shows:
- 2024-01-15 data appears at 2024-01-17 14:30
- 2024-01-16 data appears at 2024-01-17 14:30
```

### After (Python Backfill)
```
✅ Historical data at correct timestamps
Energy Dashboard shows:
- 2024-01-15 data spread across 2024-01-15 timestamps
- 2024-01-16 data spread across 2024-01-16 timestamps
```

## 🛡️ Safety Features

- **Transaction-based** - All database operations in transactions (rollback on error)
- **Time-range deletion** - Only removes data in the specific time range being updated
- **Validation** - Checks database existence and sensor configuration before operation
- **Error handling** - Comprehensive error handling with detailed logging

## 🔄 Comparison: Python vs External ha-backfill

| Feature | Python Backfill | External ha-backfill |
|---------|----------------|---------------------|
| **Home Assistant OS** | ✅ Works perfectly | ❌ Requires compilation |
| **Installation** | ✅ Built-in | ❌ Manual Go compilation |
| **Dependencies** | ✅ None | ❌ Go, git, build tools |
| **Permissions** | ✅ Addon permissions | ❌ Root access needed |
| **Maintenance** | ✅ Auto-updated with addon | ❌ Manual updates |
| **Safety** | ✅ Transaction-based | ⚠️ Direct SQL execution |

## 🎯 Recommended Setup for Home Assistant OS

1. **Use Python Backfill** (default, no external tools needed)
2. **Find your sensor metadata ID** using the diagnostic script
3. **Configure your addon** with the metadata ID
4. **Test with mock data** to verify everything works
5. **Enable and enjoy** automatic timestamp correction!

## 🚀 Quick Commands

```bash
# Test functionality (safe, works anywhere)
python test_backfill_simple.py

# Show installation options
python backfill_setup.py install

# Test your setup (run on Home Assistant system)
python backfill_setup.py test

# Test with mock data (safe)
python backfill_setup.py run-test
```

## 🎉 Success!

With Python backfill enabled, your WNSM addon will:
- ✅ Automatically detect historical vs recent data
- ✅ Use MQTT for real-time updates (< 24 hours)
- ✅ Use Python backfill for historical data (> 24 hours)
- ✅ Insert data with correct timestamps directly into Home Assistant database
- ✅ Work perfectly with Home Assistant OS restrictions

Your energy data will finally appear at the right times in the Energy Dashboard! 📈⏰

## 🔗 Related Files

- `src/wnsm_sync/backfill/python_backfill.py` - Pure Python implementation
- `test_backfill_simple.py` - Functionality tests
- `backfill_setup.py` - Setup wizard and diagnostics
- `BACKFILL_GUIDE.md` - Detailed documentation