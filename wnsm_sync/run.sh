#!/bin/bash
set -e

export WNSM_USERNAME="$WNSM_USERNAME"
export WNSM_PASSWORD="$WNSM_PASSWORD"
export WNSM_GP="$WNSM_GP"
export WNSM_ZP="$WNSM_ZP"
export HA_TOKEN="$HA_TOKEN"
export HA_URL="$HA_URL"
export STAT_ID="$STAT_ID"

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
