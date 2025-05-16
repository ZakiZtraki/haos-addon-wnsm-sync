#!/bin/bash
set -e

echo "Starting sync via run.sh..."

export WNSM_USERNAME="$WNSM_USERNAME"
export WNSM_PASSWORD="$WNSM_PASSWORD"
export WNSM_GP="$WNSM_GP"
export WNSM_ZP="$WNSM_ZP"
export HA_TOKEN="$HA_TOKEN"
export HA_URL="$HA_URL"
export STAT_ID="$STAT_ID"

# Debug the environment before running the script
echo "DEBUG: Username: ${WNSM_USERNAME}"
echo "DEBUG: Password length: #{${WNSM_PASSWORD}}"
echo "DEBUG: GP: ${WNSM_GP}"
echo "DEBUG: ZP: ${WNSM_ZP}"
echo "DEBUG: HA_URL: ${HA_URL}"
echo "DEBUG: STAT_ID: ${STAT_ID}"

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
