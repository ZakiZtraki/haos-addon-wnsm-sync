import sys
print("==== Add-on starting up ====")
import os
import json
import requests
from datetime import datetime, timedelta
from decimal import Decimal
import paho.mqtt.publish as publish

# === CONFIGURATION ===
USERNAME = os.getenv("WNSM_USERNAME")
PASSWORD = os.getenv("WNSM_PASSWORD")
GP = os.getenv("WNSM_GP")
ZP = os.getenv("WNSM_ZP")
HA_URL = os.getenv("HA_URL", "http://homeassistant:8123")
HA_TOKEN = os.getenv("SUPERVISOR_TOKEN") or os.getenv("HASSIO_TOKEN") or os.getenv("HA_TOKEN")
STATISTIC_ID = os.getenv("STAT_ID", "sensor.wiener_netze_energy")
MQTT_HOST = os.getenv("MQTT_HOST", "homeassistant")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "smartmeter/energy/state")

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

# === Prepare and publish via MQTT ===
total = Decimal(0)
statistics = []

for entry in bewegungsdaten["values"]:
    ts = datetime.fromisoformat(entry["zeitpunktVon"].replace("Z", "+00:00"))
    value_kwh = Decimal(str(entry["wert"]))
    total += value_kwh
    statistics.append({
        "start": ts.isoformat(),
        "sum": float(total),
        "state": float(value_kwh)
    })

print(f"🔍 Publishing {len(statistics)} entries to MQTT topics under '{MQTT_TOPIC}/<timestamp>'")

for s in statistics:
    topic = f"{MQTT_TOPIC}/{s['start'][:16]}"  # e.g. smartmeter/energy/state/2025-05-16T00:15
    payload = {
        "value": s["sum"],
        "timestamp": s["start"]
    }
    publish.single(
        topic,
        payload=json.dumps(payload),
        hostname=MQTT_HOST,
        retain=True
    )

print("✅ All entries published to MQTT.")
