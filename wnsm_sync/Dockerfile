FROM python:3.12.10-slim

WORKDIR /app

# Install jq for JSON parsing
RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

# Install required Python packages
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy Smartmeter API module and sync script
COPY api /app/api
COPY sync_bewegungsdaten_to_ha.py /app/sync_bewegungsdaten_to_ha.py

# Copy changelog for Home Assistant UI visibility
COPY CHANGELOG.md /app/CHANGELOG.md

# Entrypoint
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh
CMD ["/app/run.sh"]
