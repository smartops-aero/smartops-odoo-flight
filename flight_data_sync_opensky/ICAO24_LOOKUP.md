# ICAO24 Automatic Lookup Feature

## Overview

The `flight_data_sync_opensky` module now includes **automatic ICAO24 lookup** functionality. When syncing flights, if an aircraft doesn't have an ICAO24 address set, the module will automatically attempt to look it up from the OpenSky Network aircraft database using the aircraft's registration number.

## How It Works

### 1. **Flight Module Enhancement**
A new optional field `icao24` has been added to the `flight.aircraft` model in the base `flight` module:

```python
icao24 = fields.Char(
    "ICAO24 Address",
    size=6,
    tracking=True,
    help="ICAO 24-bit address in hexadecimal format (e.g., ABC123). "
    "Required for flight data synchronization with services like OpenSky Network.",
)
```

This field appears in the aircraft form view between Serial Number and Model.

### 2. **OpenSky Client Lookup Method**
A new method `lookup_aircraft_by_registration()` was added to the `OpenSkyClient` class:

```python
client.lookup_aircraft_by_registration("N12345")
# Returns: {'icao24': 'abc123', 'registration': 'N12345', ...}
```

This method queries the OpenSky Network aircraft database using an undocumented metadata endpoint:
```
GET /api/metadata/aircraft/registration/{registration}
```

### 3. **Automatic Lookup in Wizard**
When you use the sync wizard, it now:

1. **Checks for ICAO24** on the aircraft record
2. **If not found**, attempts automatic lookup using the registration number
3. **If found**, saves the ICAO24 to the aircraft record for future use
4. **If not found**, shows a helpful error message with manual options

## User Experience

### Before (Required Manual Entry):
```
User → Opens wizard → Selects aircraft without ICAO24
→ Error: "Aircraft N12345 does not have ICAO24 set"
→ User must manually look up and enter ICAO24
→ User returns to wizard and tries again
```

### Now (Automatic Lookup):
```
User → Opens wizard → Selects aircraft without ICAO24
→ Module automatically looks up ICAO24 from registration
→ ICAO24 found and saved to aircraft
→ Sync proceeds automatically
→ All future syncs use the saved ICAO24 (no lookup needed)
```

## Configuration Options

### Option 1: Let the Module Handle It (Recommended)
1. Create aircraft with just **Registration number**
2. Use the sync wizard
3. Module automatically looks up and saves ICAO24
4. Done!

### Option 2: Manual ICAO24 Entry
1. Look up ICAO24 manually on [OpenSky Network](https://opensky-network.org/aircraft-database)
2. Enter it in the aircraft form
3. No lookup needed when syncing

### Option 3: Hybrid Approach
1. Let the module auto-lookup for most aircraft
2. Manually set ICAO24 for aircraft not in OpenSky database
3. Best of both worlds

## Technical Details

### Lookup API Endpoint
The module uses an undocumented OpenSky Network endpoint:
```
https://opensky-network.org/api/metadata/aircraft/registration/{registration}
```

**Note**: This is an undocumented feature and may change. The module gracefully handles failures by:
- Logging warnings instead of crashing
- Providing clear error messages to users
- Allowing manual ICAO24 entry as fallback

### Caching Strategy
- ICAO24 is looked up **once** per aircraft
- Result is **saved** to the aircraft record
- Future syncs **reuse** the saved ICAO24
- No repeated API calls for the same aircraft

### Error Handling

| Scenario | Behavior |
|----------|----------|
| Registration found in database | ICAO24 saved, sync proceeds |
| Registration not found | Clear error with manual instructions |
| Network error during lookup | Warning logged, user notified |
| No registration or ICAO24 set | Error requesting one or the other |
| ICAO24 already set | No lookup, uses existing value |

## Benefits

✅ **User-Friendly**: Works automatically without manual ICAO24 entry
✅ **Efficient**: Looks up once, uses cached value forever
✅ **Resilient**: Graceful fallback to manual entry if lookup fails
✅ **Transparent**: Logs all lookups for troubleshooting
✅ **Non-Intrusive**: Doesn't slow down syncs when ICAO24 is already set

## Limitations

⚠️ **Database Coverage**: Not all aircraft registrations are in OpenSky's database
⚠️ **Undocumented API**: The lookup endpoint is not officially documented
⚠️ **Network Dependency**: Requires internet access for first-time lookup
⚠️ **Registration Accuracy**: Requires correct registration number formatting

## Future Enhancements

Potential improvements for future versions:

1. **Manual Lookup Button**: Add "Lookup ICAO24" button in aircraft form
2. **Batch Lookup**: Look up ICAO24 for multiple aircraft at once
3. **Alternative Sources**: Use other databases if OpenSky lookup fails
4. **Offline Database**: Cache common ICAO24→registration mappings
5. **Registration Validation**: Validate registration format before lookup

## Migration from Previous Version

If you were using the module before this feature:

1. **Upgrade both modules**:
   ```bash
   odoo-bin -c odoo.conf -d your_db -u flight,flight_data_sync_opensky
   ```

2. **Existing aircraft with ICAO24**: No action needed, continues to work

3. **Existing aircraft without ICAO24**:
   - Next sync will attempt automatic lookup
   - ICAO24 will be saved if found
   - Manual entry required if not found

## Troubleshooting

### "Could not find ICAO24 address for aircraft registration N12345"

**Cause**: Registration not in OpenSky database

**Solutions**:
1. Verify registration is correct (check for typos, spaces, hyphens)
2. Look up ICAO24 manually on [OpenSky Network](https://opensky-network.org/aircraft-database)
3. Try alternative lookup sources (FlightAware, FlightRadar24)
4. Set ICAO24 manually in aircraft form

### Lookup is slow

**Cause**: First-time lookup queries external API

**Solutions**:
- Be patient (usually takes 2-5 seconds)
- After first lookup, ICAO24 is cached (no delay on future syncs)
- Set ICAO24 manually if you sync the same aircraft frequently

### Some aircraft lookups succeed, others fail

**Cause**: Inconsistent database coverage

**Solution**: This is normal. OpenSky's database doesn't have all aircraft. Manually set ICAO24 for those that fail.

## API Credits Usage

The lookup feature uses OpenSky API credits:
- **Per lookup**: ~1 API credit
- **Per aircraft**: Looked up once, then cached
- **No repeated lookups**: Uses saved ICAO24 for subsequent syncs

**Example**:
- 10 aircraft without ICAO24
- First sync: ~10 API credits used for lookups
- All future syncs: 0 additional credits (uses cached values)

## Support

For issues with ICAO24 lookup:
1. Check Odoo logs for detailed error messages
2. Verify aircraft registration is correct
3. Try manual ICAO24 entry as workaround
4. Report persistent issues on GitHub

---

**Version**: 1.0.0
**Date**: 2024-12-04
**Author**: Apexive Solutions LLC
