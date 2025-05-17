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
HA_URL = os.getenv("HA_URL", "http://supervisor/core")
HA_TOKEN = os.getenv("SUPERVISOR_TOKEN") or os.getenv("HASSIO_TOKEN") or os.getenv("HA_TOKEN")
STATISTIC_ID = os.getenv("STAT_ID", "sensor.wiener_netze_energy")

print("Using username:", os.getenv("WNSM_USERNAME"))
print("Password set?:", "YES" if os.getenv("WNSM_PASSWORD") else "NO")
print("[DEBUG] HA_URL =", HA_URL)
print("[DEBUG] Token present?:", bool(HA_TOKEN))
print("[DEBUG] STAT_ID =", STATISTIC_ID)

for k, v in os.environ.items():
    if "HA" in k or "TOKEN" in k:
        print(f"{k} = {v}")

# If any are missing, fall back to options.json
if not all([USERNAME, PASSWORD, GP, ZP, HA_URL, HA_TOKEN, STATISTIC_ID]):
    print("[WARN] One or more env vars missing — loading from /data/options.json")
    with open("/data/options.json") as f:
        opts = json.load(f)
    USERNAME = opts.get("WNSM_USERNAME", USERNAME)
    PASSWORD = opts.get("WNSM_PASSWORD", PASSWORD)
    GP = opts.get("WNSM_GP", GP)
    ZP = opts.get("WNSM_ZP", ZP)
    HA_URL = opts.get("HA_URL", HA_URL)
    STATISTIC_ID = opts.get("STAT_ID", STATISTIC_ID)
    HA_TOKEN = os.getenv("SUPERVISOR_TOKEN", HA_TOKEN)
    print("Using username:", USERNAME)
    print("Password set?:", "YES" if PASSWORD else "NO")

from api.client import Smartmeter

# === Login & Data Fetch ===
client = Smartmeter(USERNAME, PASSWORD)
client.login()

yesterday = datetime.utcnow().date() - timedelta(days=1)
from_ts = datetime.combine(yesterday, datetime.min.time()).isoformat() + "Z"
to_ts = datetime.combine(yesterday, datetime.max.time()).isoformat() + "Z"

from datetime import date

date_from = datetime.fromisoformat(from_ts.replace("Z", "")).date()
date_until = datetime.fromisoformat(to_ts.replace("Z", "")).date()

bewegungsdaten = client.bewegungsdaten(
    zaehlpunktnummer=ZP,
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
    "statistic_id": STATISTIC_ID,
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
    "Authorization": f"Bearer {os.getenv('HA_TOKEN')}",
    "Content-Type": "application/json"
}

print("🔍 Final headers:", headers)

if not HA_URL or not STATISTIC_ID:
    print(f"❌ Cannot post: HA_URL or STAT_ID is missing — HA_URL={HA_URL}, STAT_ID={STATISTIC_ID}")
    sys.exit(1)


print(f"🔍 Uploading {len(statistics)} entries to {HA_URL}/api/recorder/statistics")

print(f"🔍 Final HA_URL: {HA_URL}")
print(f"🔍 Final STAT_ID: {STATISTIC_ID}")
print(f"🔍 Final Token present?: {'Yes' if HA_TOKEN else 'No'}")

resp = requests.post(f"{HA_URL}/api/recorder/statistics", headers=headers, data=json.dumps(payload))

if resp.status_code == 200:
    print("✅ Data uploaded to Home Assistant successfully.")
else:
    print(f"❌ Upload failed: {resp.status_code} — {resp.text}")