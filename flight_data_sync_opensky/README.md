# Flight Data Sync - OpenSky Network

Synchronize flight data with the OpenSky Network API for Odoo.

## Overview

This module integrates Odoo with the [OpenSky Network](https://opensky-network.org/), a non-profit association that provides free access to real-time and historical ADS-B flight data for research and non-commercial use.

## Features

- **Interactive Sync Wizard**: User-friendly wizard for comparing and syncing flights
- **Two Sync Modes**:
  - Sync specific existing flights
  - Sync all flights for an aircraft within a date range (max 30 days)
- **Smart Comparison**: Compare OpenSky data with existing Odoo flights
- **Flexible Actions**: Choose to create, update, or skip each flight
- **Automatic Matching**: Match flights by aircraft, date, departure, and arrival
- **Flight Details**: See OpenSky flight times, duration, and callsigns

## Installation

### Requirements

- Odoo 18.0
- `flight` module (base flight management)
- `flight_data_sync` module
- Python package: `requests`

### Install

1. Install the required Python package:
   ```bash
   pip install requests
   ```

2. Install the module in Odoo:
   ```
   Settings → Apps → Update Apps List
   Search for "Flight Data Sync - OpenSky Network"
   Click Install
   ```

## Configuration

### 1. Create OpenSky Network Provider

Navigate to: **Flights → Configuration → Data Providers → Create**

- **Name**: Choose a descriptive name (e.g., "OpenSky Network")
- **Service**: Select "OpenSky Network"
- **Username** (optional): Your OpenSky Network username
- **Password** (optional): Your OpenSky Network password
- **API Base** (optional): Leave empty to use default endpoint

**Note**: While username/password are optional, authenticated users get higher API rate limits:
- Anonymous: ~400 API credits/day
- Authenticated: ~4000 API credits/day

Create a free account at [opensky-network.org](https://opensky-network.org) to increase your rate limits.

### 2. Configure Aircraft ICAO24 Addresses

**REQUIRED**: Aircraft must have ICAO24 addresses set for synchronization.

The ICAO24 address is a unique 6-character hexadecimal code assigned to each aircraft transponder (e.g., "ABC123", "3C6444").

#### Option 1: Manual Entry (Recommended)

1. Navigate to: **Flights → Configuration → Aircraft**
2. Edit each aircraft
3. Set the **ICAO24** field (6-character hex code, e.g., "ABC123")

**Finding ICAO24 addresses**:
- [OpenSky Network aircraft database](https://opensky-network.org/aircraft-database)
- [FlightAware](https://flightaware.com) - Search by registration
- [FlightRadar24](https://flightradar24.com) - Search by registration
- Aviation databases and registries

#### Option 2: Experimental Automatic Lookup

⚠️ **WARNING**: The automatic lookup feature is **experimental** and may not work reliably.

The module attempts to automatically look up ICAO24 addresses from the registration number using an **undocumented** OpenSky endpoint. This feature:
- ✅ Works automatically in the background
- ⚠️ Uses an unofficial API endpoint that may be removed
- ⚠️ May fail for many aircraft (not all are in the database)
- ⚠️ Requires internet access
- ⚠️ May be slow or timeout

**How it works**:
1. You sync an aircraft with only registration number set
2. Module attempts automatic lookup
3. If successful, ICAO24 is saved to aircraft record
4. If failed, you get a clear error message with manual instructions

**Recommendation**: For production use, manually set ICAO24 addresses to ensure reliability.

## Usage

### Using the Sync Wizard

#### From Flight List View

1. Navigate to: **Flights → Flights**
2. Click the **Action** menu (⚙️)
3. Select **"Sync with OpenSky Network"**

#### Sync by Aircraft and Date Range

1. In the wizard, select **"Sync Aircraft by Date Range"**
2. Choose:
   - **OpenSky Provider**: Select your configured provider
   - **Aircraft**: Select the aircraft to sync
   - **Date From**: Start date for sync
   - **Date To**: End date for sync (max 30 days from start)
3. Click **"Fetch Flights"**
4. Review the comparison table:
   - **Status**: "New" or "Existing"
   - **Flight details**: Date, aircraft, departure, arrival
   - **OpenSky data**: First seen, last seen, duration, callsign
   - **Action**: Choose "Create", "Update", or "Skip"
5. Adjust actions as needed
6. Click **"Apply Sync"**

#### Sync Specific Flights

1. In the wizard, select **"Sync Specific Flights"**
2. Choose:
   - **OpenSky Provider**: Select your configured provider
   - **Flights to Sync**: Select one or more existing flights
3. Click **"Fetch Flights"**
4. Review and apply as above

### Understanding the Comparison Table

The comparison table shows:

| Column | Description |
|--------|-------------|
| **Status** | "New" (not in Odoo) or "Existing" (already in Odoo) |
| **Date** | Flight date (UTC) |
| **Aircraft** | Aircraft registration |
| **Departure** | Departure aerodrome ICAO code |
| **Arrival** | Arrival aerodrome ICAO code |
| **First Seen** | UTC timestamp when OpenSky first detected the flight |
| **Last Seen** | UTC timestamp when OpenSky last detected the flight |
| **Duration** | Flight duration in hours |
| **Callsign** | Flight callsign from OpenSky (if available) |
| **Existing Flight** | Link to existing Odoo flight (if found) |
| **Action** | What to do: Create, Update, or Skip |

### Actions Explained

- **Create**: Create a new flight in Odoo from OpenSky data
- **Update**: Confirm match with existing flight (future: update times)
- **Skip**: Don't sync this flight

## API Rate Limits

The OpenSky Network API has rate limits:

### Anonymous Users
- ~400 API credits per day
- Limited to public endpoints
- No historical data older than 30 days

### Authenticated Users
- ~4000 API credits per day (10x more)
- Access to all endpoints
- Better historical data access

### Best Practices
- Use authentication for production use
- Limit date ranges to necessary periods
- Sync during off-peak hours if possible
- Monitor your API usage

## Limitations

Based on the [official OpenSky Network REST API documentation](https://openskynetwork.github.io/opensky-api/rest.html):

1. **Date Range**: **Maximum 2 days** per sync for `/flights/aircraft` endpoint (official API limitation)
2. **Historical Data**: Only flights from **previous day or earlier** available (batch processed nightly)
3. **Tracks**: Only available for last 30 days
4. **Airport Coverage**: OpenSky estimates may not match all airports perfectly
5. **ICAO24 Required**: Aircraft MUST have ICAO24 addresses (no official lookup API)
6. **Automatic Lookup**: Experimental feature using undocumented endpoint - may not work
7. **Aerodrome Matching**: Departure/arrival aerodromes must exist in Odoo
8. **Non-Commercial Use**: OpenSky data is for research/non-commercial use only
9. **Rate Limits**: 400 credits/day (anonymous) or 4000 credits/day (authenticated)

## Troubleshooting

### "Could not find ICAO24 address for aircraft registration"
- **Cause**: The aircraft's registration number is not in the OpenSky database
- **Solutions**:
  1. Verify the registration number is correct in the aircraft form
  2. Manually look up the ICAO24 on [OpenSky Network](https://opensky-network.org/aircraft-database)
  3. Set the ICAO24 field manually in the aircraft form
  4. Try a different data source if the aircraft is very new or rare

### "No flights found"
- Possible causes:
  - Aircraft didn't fly during the date range
  - Aircraft ICAO24 is incorrect
  - Flights outside OpenSky coverage area
  - API rate limit reached
- Solution: Verify ICAO24, check date range, try with authentication

### "Departure aerodrome XXX not found"
- Solution: Create the aerodrome in Odoo first (Flights → Configuration → Aerodromes)

### "Date range cannot exceed 30 days"
- Solution: Split your sync into multiple smaller date ranges

### API Errors
- Check your credentials if using authentication
- Verify internet connectivity
- Check OpenSky Network status
- Review Odoo logs for detailed error messages

## Technical Details

### Architecture

```
┌─────────────────────────────────────┐
│   OpenSky Sync Wizard (UI)         │
│   - User selects mode & parameters  │
│   - Displays comparison table       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   OpenSky Client (API Layer)       │
│   - Handles HTTP requests           │
│   - Parses JSON responses           │
│   - Manages authentication          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   OpenSky Network API               │
│   - /flights/aircraft endpoint      │
│   - Returns flight data             │
└─────────────────────────────────────┘
```

### Data Flow

1. User opens wizard and selects parameters
2. Wizard calls OpenSky client to fetch flights
3. Client queries OpenSky Network API
4. API returns flight data (JSON)
5. Wizard creates comparison lines
6. User reviews and selects actions
7. Wizard creates/updates flights in Odoo

### OpenSky API Endpoints Used

- **GET /flights/aircraft**: Fetch flights by ICAO24 and time range
  - Parameters: `icao24`, `begin`, `end` (Unix timestamps)
  - Returns: Array of flight objects

### Flight Matching Logic

Flights are matched between OpenSky and Odoo using:

1. **Aircraft**: ICAO24 address (case-insensitive)
2. **Date**: Flight date derived from `firstSeen` timestamp
3. **Departure**: ICAO aerodrome code
4. **Arrival**: ICAO aerodrome code

All four must match for a flight to be considered "Existing".

## Development

### Running Tests

```bash
# Run all tests for this module
odoo-bin --test-enable --stop-after-init \
  --test-tags=flight_data_sync_opensky \
  -d test_database -u flight_data_sync_opensky

# Run specific test
odoo-bin --test-enable --stop-after-init \
  --test-tags=flight_data_sync_opensky.test_opensky_client \
  -d test_database -u flight_data_sync_opensky
```

### Module Structure

```
flight_data_sync_opensky/
├── models/
│   ├── opensky_client.py          # OpenSky API client
│   └── flight_data_provider.py    # Provider extension
├── wizard/
│   ├── opensky_sync_wizard.py     # Sync wizard models
│   └── opensky_sync_wizard_views.xml  # Wizard views
├── views/
│   └── flight_data_provider_views.xml  # Provider info panel
├── security/
│   └── ir.model.access.csv        # Access rights
├── tests/
│   ├── test_opensky_client.py     # Client tests
│   └── test_opensky_sync.py       # Wizard tests
└── __manifest__.py
```

## License

LGPL-3

## Credits

**Author**: Apexive Solutions LLC

**Contributors**:
- OpenSky Network for providing free ADS-B data

**References**:
- OpenSky Network: https://opensky-network.org/
- API Documentation: https://openskynetwork.github.io/opensky-api/
- Citation: Schäfer, M., Strohmeier, M., Lenders, V., Martinovic, I., & Wilhelm, M. (2014).
  "Bringing Up OpenSky: A Large-scale ADS-B Sensor Network for Research." IPSN-14 Proceedings.

## Support

For issues and questions:
- GitHub: https://github.com/smartops-aero/smartops-odoo-flight
- Email: support@apexive.com
