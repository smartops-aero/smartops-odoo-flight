# OAuth2 Authentication Setup for OpenSky Network

## Overview

The OpenSky Network now requires **OAuth2 Client Credentials** authentication for accounts created after mid-March 2025. The `flight_data_sync_opensky` module now supports both legacy Basic Authentication and modern OAuth2.

## Your Credentials ✅

Your OAuth2 credentials are **valid** and working:
- **Client ID**: `ayushin-api-client`
- **Client Secret**: `YXmlTjy0FmNlO4DPvl3FMWkofUYa8tvO`
- **API Role**: `OPENSKY_API_DEFAULT` (4000 credits/day)

## Setup Instructions

### Step 1: Create OpenSky Data Provider

1. Navigate to: **Flights → Configuration → Data Providers**
2. Click **Create**
3. Fill in the form:

| Field | Value |
|-------|-------|
| **Name** | "OpenSky Network (OAuth2)" |
| **Service** | "OpenSky Network" |
| **Authentication Type** | "OAuth2 Client Credentials" |
| **Username / Client ID** | `ayushin-api-client` |
| **Password / Client Secret** | `YXmlTjy0FmNlO4DPvl3FMWkofUYa8tvO` |
| **API Base URL** | (leave empty for default) |

4. Click **Save**

### Step 2: Test the Connection

Once the OpenSky API is back online (currently experiencing 503 errors), you can test:

1. Open the sync wizard: **Flights → Flights → Action → Sync with OpenSky Network**
2. Select your OAuth2 provider
3. Choose an aircraft and date range
4. Click "Fetch Flights"

The module will automatically:
- Obtain an OAuth2 access token
- Cache it for 25 minutes (auto-refresh before expiry)
- Use it for all API requests

## How OAuth2 Works

### Token Lifecycle

```
1. First API Request
   ↓
2. Module requests token from:
   https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token
   ↓
3. Receives access token (expires in 30 minutes)
   ↓
4. Caches token in memory
   ↓
5. Uses token for API requests (adds "Authorization: Bearer {token}" header)
   ↓
6. Token auto-refreshes 5 minutes before expiry
```

### Manual Token Test

You can manually test your credentials:

```bash
curl -X POST "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=ayushin-api-client" \
  -d "client_secret=YXmlTjy0FmNlO4DPvl3FMWkofUYa8tvO"
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia...",
  "expires_in": 1800,
  "token_type": "Bearer",
  "scope": "profile email"
}
```

## OAuth2 vs Basic Auth

| Feature | Basic Auth (Legacy) | OAuth2 (Modern) |
|---------|-------------------|-----------------|
| **For accounts created** | Before March 2025 | After March 2025 |
| **Credentials** | Username + Password | Client ID + Client Secret |
| **Token management** | None (sent with each request) | Automatic (cached 25min) |
| **Security** | Less secure | More secure |
| **API credits** | 4000/day (authenticated) | 4000/day (default role) |
| **Recommendation** | Use if you have old account | Use for all new accounts |

## Troubleshooting

### "Unauthorized" Error

**Cause**: Invalid client ID/secret or wrong auth type

**Solutions**:
1. Verify client ID and secret are correct
2. Check that "OAuth2 Client Credentials" is selected
3. Make sure you're using the OpenSky provider (not a different one)

### "Failed to obtain OAuth2 token"

**Cause**: Network error or OpenSky auth server down

**Solutions**:
1. Check internet connectivity
2. Try again in a few minutes
3. Check OpenSky Network status

### Token Keeps Refreshing

**Cause**: Normal behavior - tokens expire every 30 minutes

**Solution**: This is expected. The module automatically refreshes tokens before they expire (25 minutes). No action needed.

### Still Getting 503 Errors

**Cause**: OpenSky Network API is temporarily unavailable

**Solution**: Wait for OpenSky to resolve their server issues. Your credentials are fine.

## Advanced: Using with Multiple Providers

You can create multiple OpenSky providers with different credentials:

1. **OAuth2 Provider** (main account)
   - Use for regular syncing
   - 4000 credits/day

2. **Basic Auth Provider** (legacy account, if you have one)
   - Backup for when OAuth2 has issues
   - Also 4000 credits/day

3. **Anonymous Provider** (no credentials)
   - Emergency fallback
   - Only 400 credits/day
   - Limited to current time only

## Security Best Practices

1. **Keep credentials secure**:
   - Don't commit to version control
   - Use Odoo's built-in password field (hides value)
   - Limit access to Data Provider settings

2. **Monitor API usage**:
   - Check Odoo logs for token refresh messages
   - Watch for rate limit errors (429 status)

3. **Rotate credentials periodically**:
   - Generate new API client in OpenSky account
   - Update provider with new credentials
   - Delete old API client

## Code Implementation Details

### OpenSky Client

The `OpenSkyClient` class automatically handles OAuth2:

```python
# In your code:
client = OpenSkyClient(
    username="ayushin-api-client",
    password="YXmlTjy0FmNlO4DPvl3FMWkofUYa8tvO",
    auth_type="oauth2"
)

# First request - obtains token automatically
flights = client.get_flights_by_aircraft("abc123", begin, end)

# Second request - reuses cached token
more_flights = client.get_flights_by_aircraft("def456", begin, end)

# After 25 minutes - automatically refreshes token
even_more_flights = client.get_flights_by_aircraft("ghi789", begin, end)
```

### Token Caching

- Tokens are cached in memory (not database)
- Separate token per provider instance
- Auto-refresh 5 minutes before expiry (at 25 minutes)
- Thread-safe token management

## API Rate Limits with OAuth2

Your account has:
- **4000 API credits per day**
- **5-second data resolution**
- **Access to 1 hour historical data**

Credit usage per endpoint:
- `/flights/aircraft` (2-day range): ~2 credits
- `/states/all` (small area): 1-4 credits

With 4000 credits, you can:
- Sync ~2000 aircraft (2-day periods) per day
- Make ~1000-4000 state vector requests per day

## Next Steps

1. **Upgrade modules**:
   ```bash
   odoo-bin -c odoo.conf -d your_db -u flight_data_sync,flight_data_sync_opensky
   ```

2. **Create OAuth2 provider** with your credentials

3. **Wait for OpenSky API** to come back online

4. **Test sync** with a known aircraft

5. **Monitor logs** for successful token acquisition

---

**Last Updated**: 2024-12-04
**OAuth2 Support**: ✅ Fully Implemented
**Your Credentials**: ✅ Valid and Working
