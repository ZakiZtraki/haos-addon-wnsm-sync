import sys
import os
import json
import requests
from datetime import datetime, timedelta
from decimal import Decimal

from api.client import Smartmeter

# === CONFIGURATION ===
USERNAME = os.getenv("WNSM_USERNAME")
PASSWORD = os.getenv("WNSM_PASSWORD")
GP = os.getenv("WNSM_GP")
ZP = os.getenv("WNSM_ZP")
HA_URL = os.getenv("HA_URL", "https://haos.zenmedia.live")
HA_TOKEN = os.getenv("HA_TOKEN")
STATISTIC_ID = os.getenv("STAT_ID", "sensor.wiener_netze_energy")

# === Login & Data Fetch ===
client = Smartmeter(USERNAME, PASSWORD)
client.login()

yesterday = datetime.utcnow().date() - timedelta(days=1)
from_ts = datetime.combine(yesterday, datetime.min.time()).isoformat() + "Z"
to_ts = datetime.combine(yesterday, datetime.max.time()).isoformat() + "Z"

bewegungsdaten = client.get_bewegungsdaten(
    GP,
    ZP,
    from_ts,
    to_ts,
    "V002"
)

# === Prepare Data for HA REST API ===
total = Decimal(0)
statistics = []

for entry in bewegungsdaten["data"]:
    ts = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
    value_kwh = Decimal(entry["energyConsumption"])
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
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}

resp = requests.post(f"{HA_URL}/api/recorder/statistics", headers=headers, data=json.dumps(payload))

if resp.status_code == 200:
    print("✅ Data uploaded to Home Assistant successfully.")
else:
    print(f"❌ Upload failed: {resp.status_code} — {resp.text}")