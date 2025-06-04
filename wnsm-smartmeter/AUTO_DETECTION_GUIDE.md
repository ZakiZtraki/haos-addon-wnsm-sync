# 🔍 Automatic Sensor Detection - Zero Configuration Required!

## 🎯 Great News!

You're absolutely right - since your WNSM addon creates the MQTT sensors through discovery, we can **automatically detect** the sensor metadata ID! **No manual configuration needed!**

## ✨ How Auto-Detection Works

### 1. **MQTT Discovery Creates Sensors**
Your addon creates these sensors via MQTT discovery:
```
sensor.wnsm_daily_total_{zp_last8}    # Daily cumulative energy (preferred for backfill)
sensor.wnsm_energy_{zp_last8}         # 15-minute energy readings
sensor.wnsm_sync_status_{zp_last8}    # Sync status
```

### 2. **Auto-Detection Logic**
The backfill system automatically:
1. **Extracts Zählpunkt** from your configuration (`ZP`)
2. **Generates expected sensor names** using the last 8 digits
3. **Queries Home Assistant database** for matching sensors
4. **Selects the best sensor** for backfill (daily total preferred)

### 3. **Zero Configuration**
```yaml
# Minimal configuration - metadata ID auto-detected!
ENABLE_BACKFILL: true
# That's it! No HA_IMPORT_METADATA_ID needed
```

## 🔧 Expected Sensor Names

For Zählpunkt: `AT0010000000000000000000001234567890`
- Last 8 digits: `34567890`
- Expected sensors:
  - `sensor.wnsm_daily_total_34567890` ← **Preferred for backfill**
  - `sensor.wnsm_energy_34567890` ← Alternative

## 🧪 Testing Auto-Detection

### Test Without Database (Safe)
```bash
python backfill_setup.py test --config test_config.json
# Shows: "💡 Or let the addon auto-detect it when running on Home Assistant"
```

### Test With Home Assistant Database
When running on your Home Assistant system:
```bash
python backfill_setup.py test
# Shows: "🔍 Auto-detected metadata ID: 14"
#        "✅ No manual configuration needed!"
```

## 📋 Configuration Options

### ✅ **Automatic (Recommended)**
```yaml
# Minimal configuration - auto-detection enabled
ENABLE_BACKFILL: true
USE_PYTHON_BACKFILL: true  # Default
# HA_IMPORT_METADATA_ID not needed - auto-detected!
```

### ⚙️ **Manual Override (Optional)**
```yaml
# If you want to specify a different sensor
ENABLE_BACKFILL: true
HA_IMPORT_METADATA_ID: "15"  # Override auto-detection
```

## 🔄 Auto-Detection Process

```
1. 📊 Addon starts with backfill enabled
    ↓
2. 🔍 Check if HA_IMPORT_METADATA_ID is configured
    ↓ (if not configured)
3. 🎯 Extract Zählpunkt from configuration
    ↓
4. 🔎 Generate expected sensor names
    ↓
5. 🗄️ Query Home Assistant database
    ↓
6. ✅ Auto-detect and use sensor metadata ID
    ↓
7. 🚀 Backfill works automatically!
```

## 📊 Sensor Selection Priority

1. **`sensor.wnsm_daily_total_{zp}`** ← **Preferred**
   - `state_class: "total_increasing"`
   - Perfect for cumulative energy backfill
   - Created by your addon's MQTT discovery

2. **`sensor.wnsm_energy_{zp}`** ← **Alternative**
   - `state_class: "measurement"`
   - 15-minute delta readings
   - Also created by your addon

## 🛡️ Fallback Behavior

If auto-detection fails:
1. **Logs helpful information** about available sensors
2. **Shows expected sensor names** for debugging
3. **Provides manual configuration option**
4. **Continues with MQTT-only mode** (no backfill)

## 🎯 Benefits

- ✅ **Zero Configuration** - Works out of the box
- ✅ **Automatic Setup** - No manual sensor ID lookup needed
- ✅ **Self-Healing** - Adapts if sensor IDs change
- ✅ **Debug Friendly** - Clear logging when auto-detection fails
- ✅ **Override Available** - Manual configuration still possible

## 🚀 Quick Start

### 1. **Enable Backfill**
```yaml
ENABLE_BACKFILL: true
```

### 2. **Deploy and Run**
The addon will automatically:
- Detect your WNSM sensors
- Find the correct metadata ID
- Enable backfill with proper timestamps

### 3. **Verify Auto-Detection**
Check the logs for:
```
INFO: Auto-detected WNSM sensor: sensor.wnsm_daily_total_34567890 (metadata_id: 14)
INFO: All prerequisites for Python backfill are met
```

## 🔍 Troubleshooting Auto-Detection

### If Auto-Detection Fails

1. **Check Zählpunkt Configuration**
   ```yaml
   ZP: "AT0010000000000000000000001234567890"  # Must be configured
   ```

2. **Verify MQTT Discovery Worked**
   - Check Home Assistant → Settings → Devices & Services
   - Look for "Wiener Netze Smart Meter" device
   - Verify energy sensors exist

3. **Check Sensor Names**
   ```bash
   python backfill_setup.py test
   # Shows available sensors and expected names
   ```

4. **Manual Override**
   ```yaml
   HA_IMPORT_METADATA_ID: "your_sensor_id"
   ```

## 🎉 Result

With auto-detection enabled:
- ✅ **No manual sensor ID lookup required**
- ✅ **Works immediately after MQTT discovery**
- ✅ **Adapts to your specific Zählpunkt**
- ✅ **Perfect timestamps for historical data**

Your WNSM addon now provides **zero-configuration backfill** that just works! 🚀📈⏰

## 🔗 Related Files

- `src/wnsm_sync/backfill/python_backfill.py` - Auto-detection implementation
- `src/wnsm_sync/mqtt/discovery.py` - MQTT sensor creation
- `backfill_setup.py` - Testing and diagnostics