# Web Timezone Switcher

Real-time timezone switching for Odoo display without database modifications.

## Overview

This module adds a **systray dropdown** that allows users to switch their display timezone in real-time without modifying any database records. All datetime fields automatically re-render in the selected timezone.

### Key Features

- ✅ **Session-based switching** - No database modifications
- ✅ **Systray integration** - Easy access from any page
- ✅ **Auto re-rendering** - Datetime fields update immediately
- ✅ **Persistent preference** - Survives page reloads via localStorage
- ✅ **User default fallback** - Gracefully falls back to user's configured timezone
- ✅ **IANA timezone support** - Full pytz timezone database
- ✅ **Search functionality** - Quick timezone lookup
- ✅ **UTC offset display** - Shows offset for each timezone
- ✅ **Current time display** - Live clock in selected timezone
- ✅ **Override indicator** - Badge shows when using non-default timezone

## Installation

1. Copy the `web_tz_switcher` module to your addons directory
2. Update the module list: `Settings → Technical → Database Structure → Update Apps List`
3. Install the module: `Apps → Search "Web Timezone Switcher" → Install`

No configuration needed - works immediately after installation!

## Usage

### Basic Usage

1. **Click the timezone dropdown** in the systray (top-right corner)
2. **Search or browse** available timezones by region
3. **Select a timezone** - All datetime fields re-render immediately
4. **Reset to default** - Click "Reset to Default" button when in override mode

### Features

#### Live Time Display

The systray shows:

- Current timezone abbreviation (e.g., "New York (14:30)")
- Live clock updating every second
- Warning badge when using override timezone

#### Smart Timezone Selection

The dropdown provides:

- **Search box** - Type to filter timezones (e.g., "york", "tokyo")
- **Regional grouping** - Timezones organized by continent
- **UTC offsets** - Each timezone shows its current UTC offset
- **Current indicator** - Checkmark shows active timezone
- **Show All Regions** - Toggle to see all available regions

#### Session Persistence

Your timezone preference:

- ✅ Persists across page navigation
- ✅ Survives browser refresh (localStorage)
- ✅ Resets after logout
- ✅ Independent per browser/device

## Technical Details

### Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (Browser)                             │
│  ┌───────────────────────────────────────────┐  │
│  │  Systray Component                        │  │
│  │  - Timezone dropdown UI                   │  │
│  │  - Search & selection                     │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  Timezone Service                         │  │
│  │  - RPC calls to backend                   │  │
│  │  - User context updates                   │  │
│  │  - View re-rendering                      │  │
│  │  - localStorage persistence               │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                    │ JSON-RPC
                    ▼
┌─────────────────────────────────────────────────┐
│  Backend (Odoo Server)                          │
│  ┌───────────────────────────────────────────┐  │
│  │  Controller                               │  │
│  │  /web/timezone/switch                     │  │
│  │  /web/timezone/reset                      │  │
│  │  /web/timezone/current                    │  │
│  │  /web/timezone/list                       │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  Session Context                          │  │
│  │  request.session.context['tz'] = 'UTC+5' │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  Database (PostgreSQL)                          │
│  - All datetime fields remain in UTC           │
│  - No user records modified                     │
│  - No timezone data stored                      │
└─────────────────────────────────────────────────┘
```

### How It Works

1. **User selects timezone** in systray dropdown
2. **Service calls backend** via `/web/timezone/switch`
3. **Backend validates** timezone against pytz database
4. **Session context updated** with `tz` parameter
5. **User context patched** via `user.updateContext({ tz })`
6. **Current view reloads** triggering datetime re-rendering
7. **Preference stored** in browser localStorage
8. **All datetime fields** now display in selected timezone

### Key Design Principles

#### ✅ No Database Modifications

```python
# ❌ NEVER does this:
user.write({'tz': 'America/New_York'})

# ✅ ONLY does this:
request.session.context['tz'] = 'America/New_York'
```

#### ✅ Session-Based Storage

```javascript
// Frontend updates user context (affects rendering only)
user.updateContext({ tz: timezone });

// Backend updates session context
request.session.context = { ...context, tz: timezone };
```

#### ✅ Graceful Fallback

```
Selected Timezone (session context)
    ↓ (if not set)
User's Default Timezone (res.users.tz)
    ↓ (if not set)
UTC
```

## API Reference

### Backend Endpoints

#### POST `/web/timezone/switch`

Switch to a new timezone.

**Request:**

```json
{
  "timezone": "America/New_York"
}
```

**Response:**

```json
{
  "success": true,
  "timezone": "America/New_York",
  "user_context": {
    "tz": "America/New_York",
    ...
  }
}
```

#### POST `/web/timezone/reset`

Reset to user's default timezone.

**Response:**

```json
{
  "success": true,
  "timezone": "UTC",
  "user_context": {...}
}
```

#### POST `/web/timezone/current`

Get current timezone information.

**Response:**

```json
{
  "timezone": "America/New_York",
  "is_override": true,
  "user_default": "UTC",
  "session_context": {...}
}
```

#### POST `/web/timezone/list`

Get available timezones.

**Request:**

```json
{
  "common_only": true
}
```

**Response:**

```json
{
  "timezones": ["America/New_York", "Europe/London", ...],
  "grouped": {
    "America": ["America/New_York", ...],
    "Europe": ["Europe/London", ...]
  },
  "count": 400
}
```

### Frontend Service

```javascript
import { useService } from "@web/core/utils/hooks";

const timezoneSwitcher = useService("timezone_switcher");

// Get current timezone
const tz = await timezoneSwitcher.getCurrentTimezone();

// Switch timezone
await timezoneSwitcher.switchTimezone("Europe/Paris");

// Reset to default
await timezoneSwitcher.resetTimezone();

// List timezones
const { timezones, grouped } = await timezoneSwitcher.listTimezones(true);
```

## Use Cases

### Aviation Operations

Perfect for flight operations spanning multiple timezones:

```
User in London (GMT) viewing:
- Flight departure: Los Angeles 10:00 PST
- Flight arrival: New York 18:00 EST

Switch to PST:
- Departure: 10:00 PST ✓
- Arrival: 15:00 PST

Switch to EST:
- Departure: 13:00 EST
- Arrival: 18:00 EST ✓
```

### Global Support Teams

Support staff can switch to customer's timezone:

```
Support Agent in India (IST):
Customer ticket timestamp: 2024-12-03 09:00 PST

Switch to PST:
Ticket created: 09:00 PST (customer's local time)
```

### Multi-Region Business

View reports in different regional timezones:

```
Sales Manager reviewing regional reports:
- APAC sales: Switch to Asia/Tokyo
- EMEA sales: Switch to Europe/London
- Americas sales: Switch to America/New_York
```

## Compatibility

- **Odoo Version:** 18.0
- **Python:** 3.10+
- **Dependencies:** `web` (core Odoo module)
- **Browser:** Modern browsers with localStorage support

## Testing

Run the included test suite:

```bash
# Run all tests
odoo-bin -c odoo.conf --test-enable --stop-after-init \
  --test-tags=web_tz_switcher -d test_db -u web_tz_switcher

# Run specific test
odoo-bin -c odoo.conf --test-enable --stop-after-init \
  --test-tags=web_tz_switcher.test_timezone_controller -d test_db
```

Test coverage:

- ✅ Valid timezone switching
- ✅ Invalid timezone handling
- ✅ Reset to default
- ✅ Session persistence
- ✅ Override flag behavior
- ✅ Timezone listing (common & all)

## Troubleshooting

### Timezone not persisting after refresh

**Cause:** localStorage disabled or browser in private mode
**Solution:** Enable localStorage or accept that timezone resets each session

### Datetime fields not updating

**Cause:** Custom datetime widgets not using Odoo's standard context
**Solution:** Ensure custom widgets read `user.context.tz`

### Timezone dropdown not appearing

**Cause:** Asset bundle not loaded
**Solution:** Clear browser cache and reload: `Ctrl+Shift+R`

### Performance issues with many datetime fields

**Cause:** Full page reload on timezone switch
**Solution:** Consider selective re-rendering (advanced customization)

## Development

### Extending the Module

#### Custom Timezone Groups

```javascript
// Customize featured regions
get featuredRegions() {
    return ["America", "Europe", "Asia", "Pacific", "Africa"];
}
```

#### Add Favorite Timezones

```javascript
// Store user's favorite timezones
const favorites = JSON.parse(localStorage.getItem("tz_favorites") || "[]");
```

#### Custom Notification Behavior

```javascript
// Customize success notification
notification.add(`Time zone changed to ${timezone}`, {
  type: "success",
  title: "Display Updated",
});
```

## Roadmap

- [ ] Favorite timezones (star/pin frequently used)
- [ ] Timezone presets (e.g., "Customer Timezone", "HQ Timezone")
- [ ] World clock widget (show multiple timezones simultaneously)
- [ ] Keyboard shortcuts (e.g., `Ctrl+Shift+T` to open dropdown)
- [ ] Recent timezones (quick access to last 5 used)
- [ ] Timezone autodetection from browser

## License

LGPL-3.0

## Author

**Apexive Solutions LLC**
Website: https://apexive.com

## Support

For issues, questions, or contributions:

- GitHub Issues: (your repository)
- Email: support@apexive.com

## Credits

Built with:

- Odoo OWL framework
- Luxon datetime library
- Python pytz library
- Bootstrap styling

---

**Remember:** This module only changes display. All database times remain in UTC! 🌍⏰
