# Installation and Quick Start Guide

## Prerequisites

1. **Odoo 18.0** installed and running
2. **flight** module installed (base flight management)
3. **flight_data_sync** module installed
4. **Python requests library** installed:
   ```bash
   pip install requests
   ```

## Installation Steps

### 1. Install the Module

```bash
# If not already in your addons path, add this directory to odoo.conf:
# addons_path = /path/to/extra-addons/.src/smartops/flight,...

# Then restart Odoo and update app list
# In Odoo UI: Settings → Apps → Update Apps List
# Search for "Flight Data Sync - OpenSky Network"
# Click Install
```

Or via command line:

```bash
odoo-bin -c odoo.conf -d your_database -i flight_data_sync_opensky
```

### 2. Create an OpenSky Network Provider

1. Navigate to: **Flights → Configuration → Data Providers**
2. Click **Create**
3. Fill in:
   - **Name**: "OpenSky Network" (or any name you prefer)
   - **Service**: Select "OpenSky Network"
   - **Username** (optional): Your OpenSky Network username
   - **Password** (optional): Your OpenSky Network password
   - **API Base** (optional): Leave empty for default

**Note**: Creating a free account at [opensky-network.org](https://opensky-network.org)
and using credentials gives you 10x more API credits (4000/day vs 400/day).

### 3. Configure Your Aircraft

For the sync to work, aircraft must have ICAO24 addresses:

1. Go to: **Flights → Configuration → Aircraft**
2. For each aircraft, set the **ICAO24** field
   - Format: 6-character hex code (e.g., "ABC123", "3C6444")
   - Case insensitive (will be normalized)

**Finding ICAO24 codes**:
- Search your aircraft registration on [FlightAware](https://flightaware.com)
- Use [OpenSky Network aircraft search](https://opensky-network.org)
- Check aviation databases like [FlightRadar24](https://flightradar24.com)

## Quick Test

### Test the Sync Wizard

1. Go to: **Flights → Flights**
2. Click the **Action** button (⚙️)
3. Select: **"Sync with OpenSky Network"**
4. Choose **"Sync Aircraft by Date Range"**
5. Select:
   - Your OpenSky provider
   - An aircraft (with ICAO24 set)
   - Today's date for both From and To
6. Click **"Fetch Flights"**

If the aircraft flew today, you should see flights appear in the comparison table!

## Example Configuration

### Example 1: Private Jet Operator

```
Provider:
  Name: OpenSky Network (Authenticated)
  Service: OpenSky Network
  Username: myuser@company.com
  Password: ••••••••

Aircraft:
  Registration: N12345
  ICAO24: ABC123

Usage:
  - Sync Mode: Aircraft Date Range
  - Date From: 2024-01-01
  - Date To: 2024-01-31 (max 30 days)
  - Result: Fetches all flights for N12345 in January
```

### Example 2: Flight School

```
Provider:
  Name: OpenSky Network (Anonymous)
  Service: OpenSky Network
  (no username/password)

Aircraft:
  Multiple training aircraft with ICAO24 codes set

Usage:
  - Sync specific flights after students report completion
  - Verify actual flight times match training logs
  - Track aircraft utilization
```

## Troubleshooting

### "Aircraft does not have an ICAO24 address set"

**Solution**: Edit the aircraft and fill in the ICAO24 field.

### "No flights found"

**Possible causes**:
- Aircraft didn't fly during the selected period
- ICAO24 code is incorrect
- Aircraft outside OpenSky coverage area
- API rate limit reached

**Solutions**:
1. Verify ICAO24 is correct
2. Try a different date range
3. Use authentication for higher limits
4. Check OpenSky coverage maps

### "Date range cannot exceed 30 days"

**Solution**: This is an OpenSky API limitation. Split your sync into multiple 30-day periods.

### "Aerodrome XXX not found"

**Solution**: Create the aerodrome first:
1. Go to: **Flights → Configuration → Aerodromes**
2. Create the missing aerodrome with correct ICAO code

## Next Steps

- Read the [README.md](README.md) for detailed documentation
- Check the [module documentation](doc/index.rst)
- Review the [test examples](tests/) for usage patterns
- Explore scheduled sync options in the provider configuration

## Support

- GitHub Issues: https://github.com/smartops-aero/smartops-odoo-flight/issues
- Documentation: See README.md
- Email: support@apexive.com
