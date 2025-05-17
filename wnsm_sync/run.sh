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

#Output all variables in the current shell
echo "Environment variables:"
env