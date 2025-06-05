# Historical Data Backfill Guide

This guide explains how to set up and use the historical data backfill feature to import energy data with correct timestamps into Home Assistant.

## Problem Statement

By default, MQTT sensor data in Home Assistant is recorded with the current timestamp when the message arrives, not the timestamp from the payload. This means that when you sync historical energy data (e.g., from the last few days), all readings appear at the current time instead of being spread across their original time periods.

## Solution: ha-backfill Integration

We've integrated with the [ha-backfill](https://github.com/aamcrae/ha-backfill) tool, which directly inserts historical data into Home Assistant's database with correct timestamps.

## How It Works

1. **Data Export**: Historical energy readings are exported to CSV files in a format compatible with ha-backfill
2. **Database Import**: The ha-backfill tool processes the CSV files and generates SQL commands
3. **Direct Insertion**: Data is inserted directly into Home Assistant's statistics tables with correct timestamps

## Setup Instructions

### Step 1: Install ha-backfill

The ha-backfill tool needs to be compiled and installed on your system.

#### Option A: Use the setup script
```bash
python3 backfill_setup.py install
```

#### Option B: Manual installation
```bash
# Install Go (if not already installed)
sudo apt update && sudo apt install golang-go

# Download and compile ha-backfill
git clone https://github.com/aamcrae/ha-backfill.git
cd ha-backfill
go build -o ha-backfill backfill.go

# Install the binary
sudo cp ha-backfill /usr/local/bin/
sudo chmod +x /usr/local/bin/ha-backfill
```

### Step 2: Sensor Detection (Automatic!)

🎉 **Great news!** Since your WNSM addon creates the sensors via MQTT discovery, the metadata ID is **automatically detected**! No manual configuration needed.

#### Automatic Detection
The addon automatically finds sensors created by MQTT discovery:
- `sensor.wnsm_daily_total_{zp_last8}` (preferred for backfill)
- `sensor.wnsm_energy_{zp_last8}` (alternative)

Where `{zp_last8}` is the last 8 digits of your Zählpunkt.

#### Manual Override (Optional)
If you want to use a different sensor or auto-detection fails:

```bash
# Find available sensors
python3 backfill_setup.py test --config /data/options.json
```

Or query the database directly:
```bash
sqlite3 /homeassistant/home-assistant_v2.db
```
```sql
SELECT id, statistic_id, source, unit_of_measurement, name
FROM statistics_meta
WHERE unit_of_measurement = 'kWh'
ORDER BY statistic_id;
```

### Step 3: Configure Backfill

Add these options to your configuration:

#### Minimal Configuration (Recommended)
```yaml
# Enable backfill functionality - that's it!
enable_backfill: true
# Sensor metadata ID is auto-detected from your MQTT discovery sensors
```

#### Advanced Configuration (Optional)
```yaml
# Enable backfill functionality
enable_backfill: true

# Use Python implementation (default, recommended for Home Assistant OS)
use_python_backfill: true

# Home Assistant database path (default: /homeassistant/home-assistant_v2.db)
ha_database_path: "/homeassistant/home-assistant_v2.db"

# Manual sensor metadata ID override (auto-detected if not specified)
# ha_import_metadata_id: "14"

# Optional: External ha-backfill binary (not needed for Python implementation)
# ha_backfill_binary: "/usr/local/bin/ha-backfill"

# Optional: Metadata IDs for export and generation (if you have them)
# ha_export_metadata_id: "13"
# ha_generation_metadata_id: "15"
```

### Step 4: Test the Setup

Test your backfill configuration:

```bash
python3 backfill_setup.py test --config /data/options.json
```

Run a test backfill with mock data:

```bash
python3 backfill_setup.py run-test --config /data/options.json
```

## Usage

### Automatic Backfill

When `enable_backfill: true` is set, the system automatically decides when to use backfill vs MQTT:

- **MQTT**: Used for recent data (less than 24 hours old, single day)
- **Backfill**: Used for historical data (older than 24 hours, multiple days)

### Manual Backfill

You can force backfill mode by running:

```python
from wnsm_sync.core.sync import WNSMSync
from wnsm_sync.config.loader import ConfigLoader

config = ConfigLoader().load_config("/data/options.json")
sync = WNSMSync(config)

# Run sync with forced backfill
sync.run_sync_cycle(force_backfill=True)
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `enable_backfill` | `false` | Enable automatic backfill for historical data |
| `ha_database_path` | `/homeassistant/home-assistant_v2.db` | Path to Home Assistant database |
| `ha_backfill_binary` | `/usr/local/bin/ha-backfill` | Path to ha-backfill executable |
| `ha_import_metadata_id` | `None` | Metadata ID for energy import sensor (required) |
| `ha_export_metadata_id` | `None` | Metadata ID for energy export sensor (optional) |
| `ha_generation_metadata_id` | `None` | Metadata ID for energy generation sensor (optional) |

## How Data is Processed

### CSV Export Format

Energy readings are converted to cumulative values and exported in this format:

```csv
#date,time,IMP,EXP,GEN-T
2024-01-15,10:00,1234.567,0.000,0.000
2024-01-15,10:15,1234.789,0.000,0.000
2024-01-15,10:30,1235.012,0.000,0.000
```

Where:
- `IMP`: Cumulative import energy (kWh)
- `EXP`: Export energy (set to 0 for WNSM data)
- `GEN-T`: Generation energy (set to 0 for WNSM data)

### Database Integration

The ha-backfill tool:
1. Deletes existing records for the specified time range
2. Inserts new records with correct timestamps
3. Updates both `statistics` and `statistics_short_term` tables

## Troubleshooting

### Common Issues

#### 1. "ha-backfill binary not found"
- Install ha-backfill following the setup instructions
- Check the path in `ha_backfill_binary` configuration

#### 2. "Home Assistant database not found"
- Verify the database path in `ha_database_path`
- Ensure Home Assistant is stopped during backfill operations

#### 3. "Import metadata ID not configured"
- Run the diagnostic script to find your sensor's metadata_id
- Set `ha_import_metadata_id` in your configuration

#### 4. "Permission denied accessing database"
- Ensure the user running the script has read/write access to the database
- Stop Home Assistant before running backfill operations

### Diagnostic Commands

Check backfill setup:
```bash
python3 backfill_setup.py test
```

View available sensors:
```bash
sqlite3 /homeassistant/home-assistant_v2.db "SELECT id, statistic_id FROM statistics_meta WHERE unit_of_measurement = 'kWh';"
```

Test ha-backfill installation:
```bash
ha-backfill -h
```

## Best Practices

### 1. Database Safety During Backfill

**For Home Assistant OS (Recommended Approach):**
The Python backfill implementation uses proper database transactions and locking, so Home Assistant doesn't need to be stopped. The backfill process:
- Uses SQLite WAL mode for concurrent access
- Implements proper transaction handling
- Uses database locks to prevent conflicts

**For Manual/External Systems:**
If running ha-backfill externally, you may need to stop Home Assistant:

```bash
# Stop Home Assistant (only for external systems)
sudo systemctl stop home-assistant

# Run backfill
python3 your_backfill_script.py

# Start Home Assistant
sudo systemctl start home-assistant
```

### 2. Backup Your Database
Before running backfill operations, backup your Home Assistant database:

```bash
cp /homeassistant/home-assistant_v2.db /homeassistant/home-assistant_v2.db.backup
```

### 3. Test with Mock Data First
Always test the backfill process with mock data before using real historical data:

```bash
python3 backfill_setup.py run-test
```

### 4. Monitor Logs
Check logs for any errors during the backfill process:

```bash
tail -f /config/home-assistant.log
```

## Integration with Energy Dashboard

After successful backfill:

1. Go to **Settings** → **Dashboards** → **Energy**
2. Your historical energy data should appear with correct timestamps
3. The energy graphs will show data spread across the correct time periods
4. Daily/weekly/monthly totals will be calculated correctly

## Limitations

1. **WNSM Data Only**: Currently supports import energy only (no export or generation)
2. **Database Access**: Requires direct access to Home Assistant database
3. **Downtime Required**: Home Assistant should be stopped during backfill operations
4. **One-Way Sync**: Backfilled data replaces existing data for the same time period

## Support

If you encounter issues:

1. Run the diagnostic script: `python3 backfill_setup.py test`
2. Check the logs for error messages
3. Verify your configuration settings
4. Ensure ha-backfill is properly installed

For more information about ha-backfill, see: https://github.com/aamcrae/ha-backfill