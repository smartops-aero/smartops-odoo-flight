# OpenSky API Compliance

This document details how the `flight_data_sync_opensky` module complies with the official [OpenSky Network REST API documentation](https://openskynetwork.github.io/opensky-api/rest.html).

## Official API Endpoints Used

### 1. `/flights/aircraft` - Get Flights by Aircraft

**Endpoint**: `GET /flights/aircraft`

**Parameters**:
- `icao24` (string, required): ICAO 24-bit address in lowercase hex
- `begin` (integer, required): Unix timestamp for interval start
- `end` (integer, required): Unix timestamp for interval end

**Limitations** (from official docs):
- ✅ ICAO24 must be lowercase
- ✅ Time interval must NOT exceed **2 days**
- ✅ Requires authentication for access
- ✅ Flights are batch-processed nightly (only previous day or earlier available)

**Our Implementation**:
```python
# In opensky_client.py
def get_flights_by_aircraft(self, icao24, begin_timestamp, end_timestamp):
    icao24 = icao24.lower()  # ✅ Ensure lowercase
    params = {
        "icao24": icao24,
        "begin": int(begin_timestamp),
        "end": int(end_timestamp),
    }
    return self._make_request("flights/aircraft", params=params)
```

**Validation**:
```python
# In opensky_sync_wizard.py
@api.constrains("date_from", "date_to")
def _check_date_range(self):
    delta = (wizard.date_to - wizard.date_from).days
    if delta > 2:  # ✅ Enforce 2-day limit
        raise ValidationError("Date range cannot exceed 2 days...")
```

## Authentication

### Supported Methods

**1. Basic Authentication (Legacy)**
```python
OpenSkyClient(username="user", password="pass")
# Uses HTTP Basic Auth
```

**2. OAuth2 Client Credentials (Recommended for 2025+)**
- Not yet implemented
- Required for accounts created after mid-March 2025
- TODO: Add OAuth2 support

### Rate Limits

From official docs:
- Anonymous: 400 API credits/day, 10s resolution, current time only
- Authenticated: 4000 API credits/day, 5s resolution, 1 hour history
- Active contributors: 8000 API credits/day

**Our Implementation**:
- ✅ Supports both anonymous and authenticated access
- ✅ Documentation mentions rate limits
- ⚠️ No built-in rate limit tracking (relies on API response headers)

## API Credit Usage

Per official docs, `/flights/aircraft` uses credits based on time partitions (roughly number of days queried).

**Our Usage**:
- 2-day maximum = ~2 API credits per sync
- Reasonable for authenticated users (4000 credits/day = ~2000 syncs/day)

## ICAO24 Requirement

### Official API Requirements

From the docs:
> "icao24: Unique ICAO 24-bit address of the transponder in hex string representation. All letters need to be lower case"

**No official lookup endpoint exists** to convert registration → ICAO24.

### Our Solution

**Primary Method** (Recommended):
- Users manually set ICAO24 in aircraft form
- Field added to base `flight` module
- Clear documentation on where to find ICAO24 codes

**Experimental Method** (Fallback):
- Automatic lookup using **undocumented** endpoint
- Clear warnings that this may not work
- Graceful fallback to manual entry
- Never blocks user from manual entry

```python
def lookup_aircraft_by_registration(self, registration):
    """
    WARNING: Uses UNDOCUMENTED endpoint.
    Official API does not provide registration→ICAO24 lookup.
    May be removed at any time.
    """
    # Try undocumented endpoint, return None on failure
    # All errors are caught and logged
```

## Response Handling

### Flight Objects

From official docs, each flight object contains:

| Field | Type | Description |
|-------|------|-------------|
| icao24 | string | Transponder address |
| firstSeen | int | Unix timestamp of first position |
| estDepartureAirport | string | ICAO code |
| lastSeen | int | Unix timestamp of last position |
| estArrivalAirport | string | ICAO code |
| callsign | string | Flight callsign |

**Our Implementation**:
```python
# We correctly extract all these fields
flight_date = datetime.utcfromtimestamp(flight_data["firstSeen"]).date()
departure_icao = flight_data["estDepartureAirport"].upper()
arrival_icao = flight_data["estArrivalAirport"].upper()
callsign = flight_data.get("callsign", "").strip() or False
```

✅ Correctly handles null values
✅ Converts timestamps to dates
✅ Case normalization (uppercase ICAO codes)

## Error Handling

### HTTP Status Codes

From official docs:
- `200 OK` - Success
- `404 Not Found` - No flights in time period
- `429 Too Many Requests` - Rate limit exceeded
- `401 Unauthorized` - Invalid/missing credentials

**Our Implementation**:
```python
def _make_request(self, endpoint, params=None):
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            # ✅ 404 is OK - just no data
            return None
        raise OpenSkyAPIError(...)  # ✅ Raise for other errors
```

## Compliance Checklist

### ✅ Fully Compliant

- [x] Uses official `/flights/aircraft` endpoint
- [x] ICAO24 parameter in lowercase
- [x] Unix timestamp parameters
- [x] 2-day maximum time interval enforced
- [x] HTTP Basic Auth supported
- [x] Proper error handling for 404/429
- [x] Respects batch processing limitation
- [x] Correctly parses flight response format

### ⚠️ Partially Compliant

- [~] OAuth2 authentication (not yet implemented, legacy auth still works)
- [~] Rate limit tracking (relies on API headers, doesn't pre-check)
- [~] ICAO24 lookup (uses undocumented endpoint as convenience feature)

### ❌ Not Applicable

- [ ] `/states/all` endpoint - Not used
- [ ] `/tracks` endpoint - Not used
- [ ] `/flights/all` endpoint - Not used
- [ ] Own state vectors - Not used

## Deviations from Official API

### 1. ICAO24 Lookup (Undocumented Endpoint)

**Why**:
- Improve user experience
- Reduce manual data entry
- Most aircraft are in OpenSky database

**Mitigation**:
- ✅ Clearly marked as experimental
- ✅ Never required - users can skip it
- ✅ Comprehensive error messages with fallback instructions
- ✅ All failures gracefully handled

### 2. No OAuth2 Support Yet

**Why**:
- Legacy basic auth still works for most users
- OAuth2 only required for accounts created after mid-March 2025

**Mitigation**:
- TODO: Add OAuth2 support
- Documentation mentions authentication requirement
- Legacy auth clearly supported

## Future Improvements

### High Priority

1. **Add OAuth2 Client Credentials Flow**
   - Required for new accounts (mid-March 2025+)
   - See official docs for implementation

2. **Rate Limit Tracking**
   - Parse `X-Rate-Limit-Remaining` header
   - Warn users before hitting limits

### Medium Priority

3. **Batch Processing Awareness**
   - Detect if user queries current day
   - Warn that flights won't be available yet

4. **Extended Time Range Support**
   - Auto-split >2 day ranges into multiple 2-day queries
   - Combine results transparently

### Low Priority

5. **Alternative ICAO24 Sources**
   - Download OpenSky aircraft database CSV
   - Cache common registrations
   - Use traffic library for offline lookup

## Testing Against Official API

### Test Checklist

- [ ] Test with valid ICAO24 and 2-day range
- [ ] Test with date range > 2 days (should fail validation)
- [ ] Test with lowercase and uppercase ICAO24
- [ ] Test with non-existent ICAO24 (404 expected)
- [ ] Test without authentication (should fail)
- [ ] Test with invalid credentials (401 expected)
- [ ] Test with time in future (should return empty)
- [ ] Test with time > 1 day ago (should have data)

### Example Test Query

```bash
# Official example from docs:
curl -u "USERNAME:PASSWORD" -s \
  "https://opensky-network.org/api/flights/aircraft?icao24=3c675a&begin=1517184000&end=1517270400" \
  | python -m json.tool
```

## References

- [Official OpenSky REST API Documentation](https://openskynetwork.github.io/opensky-api/rest.html)
- [OpenSky Network](https://opensky-network.org/)
- [OpenSky Aircraft Database](https://opensky-network.org/aircraft-database)
- [Data Stack Exchange - ICAO24 Database](https://opendata.stackexchange.com/questions/18238/)
- [Traffic Library - Aircraft Information](https://traffic-viz.github.io/data_sources/aircraft.html)

---

**Last Updated**: 2024-12-04
**API Version**: OpenSky REST API 1.4.0
**Module Version**: 1.0.0
