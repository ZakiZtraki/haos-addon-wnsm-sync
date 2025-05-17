import sys
print("==== Add-on starting up ====")
import os
import json
import requests
from datetime import datetime, timedelta
from decimal import Decimal

# === CONFIGURATION ===
USERNAME = os.getenv("WNSM_USERNAME")
PASSWORD = os.getenv("WNSM_PASSWORD")
GP = os.getenv("WNSM_GP")
ZP = os.getenv("WNSM_ZP")
HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HASSIO_TOKEN")
STATISTIC_ID = os.getenv("STAT_ID", "sensor.wiener_netze_energy")

print("Using username:", os.getenv("WNSM_USERNAME"))
print("Password set?:", "YES" if os.getenv("WNSM_PASSWORD") else "NO")

# If any are missing, fall back to options.json
if not all([USERNAME, PASSWORD, GP, ZP, HA_URL, HA_TOKEN, STATISTIC_ID]):
    print("[WARN] One or more env vars missing — loading from /data/options.json")
    with open("/data/options.json") as f:
        opts = json.load(f)
    username = opts.get("WNSM_USERNAME", USERNAME)
    password = opts.get("WNSM_PASSWORD", PASSWORD)
    gp = opts.get("WNSM_GP", GP)
    zp = opts.get("WNSM_ZP", ZP)
    ha_url = opts.get("HA_URL", HA_URL)
    stat_id = opts.get("STAT_ID", STATISTIC_ID)
    ha_token = os.getenv("SUPERVISOR_TOKEN", HA_TOKEN)
    print("Using username:", username)
    print("Password set?:", "YES" if password else "NO")

from api.client import Smartmeter

# === Login & Data Fetch ===
client = Smartmeter(username, password)
client.login()

yesterday = datetime.utcnow().date() - timedelta(days=1)
from_ts = datetime.combine(yesterday, datetime.min.time()).isoformat() + "Z"
to_ts = datetime.combine(yesterday, datetime.max.time()).isoformat() + "Z"

from datetime import date

date_from = datetime.fromisoformat(from_ts.replace("Z", "")).date()
date_until = datetime.fromisoformat(to_ts.replace("Z", "")).date()

bewegungsdaten = client.bewegungsdaten(
    zaehlpunktnummer=zp,
    date_from=date_from,
    date_until=date_until,
    aggregat="NONE"
)

# === Prepare Data for HA REST API ===
total = Decimal(0)
statistics = []

for entry in bewegungsdaten["values"]:
    ts = datetime.fromisoformat(entry["zeitpunktVon"].replace("Z", "+00:00"))
    value_kwh = Decimal(str(entry["wert"]))  # Ensure proper Decimal conversion
    total += value_kwh
    statistics.append({
        "start": ts.isoformat(),
        "sum": float(total),
        "state": float(value_kwh)
    })

metadata = {
    "statistic_id": stat_id,
    "unit_of_measurement": "kWh",
    "has_mean": False,
    "has_sum": True,
    "name": "WienerNetze Energy",
    "source": "integration"
}

payload = [{
    "metadata": metadata,
    "data": statistics
}]

headers = {
    "Authorization": f"Bearer {os.getenv('ha_token')}",
    "Content-Type": "application/json"
}

print("🔍 Final headers:", headers)

if not HA_URL or not stat_id:
    print(f"❌ Cannot post: HA_URL or STAT_ID is missing — HA_URL={ha_url}, STAT_ID={stat_id}")
    sys.exit(1)


print(f"🔍 Uploading {len(statistics)} entries to {HA_URL}/api/recorder/statistics")

print(f"🔍 Final HA_URL: {ha_url}")
print(f"🔍 Final STAT_ID: {stat_id}")
print(f"🔍 Final Token present?: {'Yes' if ha_token else 'No'}")

resp = requests.post(f"{ha_url}/api/recorder/statistics", headers=headers, data=json.dumps(payload))

if resp.status_code == 200:
    print("✅ Data uploaded to Home Assistant successfully.")
else:
    print(f"❌ Upload failed: {resp.status_code} — {resp.text}")