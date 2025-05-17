#!/bin/bash
set -e

echo "Starting sync via run.sh..."

# Forward signals to the Python process
_term() {
    echo "Caught SIGTERM, forwarding to child"
    kill -TERM "$child" 2>/dev/null
}

trap _term SIGTERM SIGINT

# Start Python script in background
python3 /app/sync_bewegungsdaten_to_ha.py &
child=$!
wait "$child"

if [ -z "$WNSM_USERNAME" ]; then
    echo "[WARN] One or more env vars missing — loading from /data/options.json"
    export WNSM_USERNAME=$(jq -r '.WNSM_USERNAME' /data/options.json)
    export WNSM_PASSWORD=$(jq -r '.WNSM_PASSWORD' /data/options.json)
    export WNSM_GP=$(jq -r '.WNSM_GP' /data/options.json)
    export WNSM_ZP=$(jq -r '.WNSM_ZP' /data/options.json)
    export HA_TOKEN=$(jq -r '.HA_TOKEN' /data/options.json)
    export HA_URL=$(jq -r '.HA_URL' /data/options.json)
    export STAT_ID=$(jq -r '.STAT_ID' /data/options.json)
fi

echo "[DEBUG] HA_URL=$HA_URL"
echo "[DEBUG] STAT_ID=$STAT_ID"