# Wiener Netze Smartmeter Sync Add-on for Home Assistant

This Home Assistant add-on fetches 15-minute interval consumption data from the Wiener Netze Smart Meter portal and injects it into Home Assistant's long-term statistics.

## Features
- Authenticates with Wiener Netze login
- Retrieves Bewegungsdaten (quarter-hourly history)
- Automatically pushes to HA statistics via REST API
- Integrates with Energy Dashboard and cost sensors
- Can be scheduled to run daily at 04:00 via automation

## Configuration
The following environment variables are required (configured via the add-on UI):

- `WNSM_USERNAME`: Your Wiener Netze login (email)
- `WNSM_PASSWORD`: Your password
- `WNSM_GP`: Geschäftspartner number
- `WNSM_ZP`: Zählpunktnummer
- `HA_TOKEN`: Home Assistant long-lived access token
- `HA_URL`: Home Assistant base URL (default: http://homeassistant.local:8123)
- `STAT_ID`: Home Assistant statistic ID (default: sensor.wiener_netze_energy)

## Installation
1. Add this repository as a custom add-on source in Home Assistant.
2. Install the `Wiener Netze Smartmeter Sync` add-on.
3. Configure credentials in the add-on UI.
4. Start the add-on or schedule it via automation.

## License
MIT © 2024 Vladimir Biryukov
