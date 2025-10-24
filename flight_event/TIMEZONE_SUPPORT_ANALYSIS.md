# Timezone Support in 16.0 RelativeDateTimePicker

## How It Worked

The 16.0 `RelativeDateTimePicker` had timezone support built into its `parseValue` method.

### Parsing Logic (Lines 75-112)

```javascript
parseValue(value, options) {
  // Regex splits input into: timeString, deltaDays, timezone
  const [timeString, deltaDays, timezone] = value.split(
    /\s*(?:([+-]\d+)|([A-Z]{3,4}))\s*$/
  );

  let parsedDate = this.baseDate || DateTime.local();
  const [hours, minutes] = timeString.split(":").map(Number);

  if (!isNaN(hours) && !isNaN(minutes)) {
    if (timezone) {
      // If timezone is present, create DateTime in that zone
      parsedDate = DateTime.fromObject(
        {
          year: parsedDate.year,
          month: parsedDate.month,
          day: parsedDate.day,
          hour: hours,
          minute: minutes,
        },
        { zone: timezone }  // ← This is the key!
      );
    } else {
      // No timezone - use local time
      parsedDate = parsedDate.set({
        hours,
        minutes,
        seconds: 0,
        milliseconds: 0,
      });
    }

    // Apply day offset if present
    if (deltaDays) {
      parsedDate = parsedDate.plus({ days: parseInt(deltaDays, 10) });
    }
  }

  return [parsedDate, false];
}
```

## Regex Pattern Explanation

```javascript
/\s*(?:([+-]\d+)|([A-Z]{3,4}))\s*$/
```

This regex matches either:
1. **Day offset**: `[+-]\d+` - Plus/minus sign followed by digits (e.g., "+1", "-2")
2. **Timezone**: `[A-Z]{3,4}` - 3-4 uppercase letters (e.g., "EST", "PST", "UTC")

### How the Split Works

```javascript
"14:30 +1".split(regex)    → ["14:30", "+1", undefined]
"14:30 EST".split(regex)   → ["14:30", undefined, "EST"]
"14:30".split(regex)       → ["14:30", undefined, undefined]
"14:30 +1 EST".split(regex) → Would only catch LAST match (EST)
```

**Note:** The regex can only capture EITHER day offset OR timezone, not both!

## Supported Input Formats

### Valid Formats

| Input | Parsed As | Description |
|-------|-----------|-------------|
| `14:30` | Same day, 2:30 PM local time | No offset, no timezone |
| `14:30 +1` | Next day, 2:30 PM local time | Day offset only |
| `08:00 -1` | Previous day, 8:00 AM local time | Negative day offset |
| `16:00 EST` | Same day, 4:00 PM Eastern Time | Timezone only |
| `09:30 UTC` | Same day, 9:30 AM UTC | UTC timezone |
| `23:45 PST` | Same day, 11:45 PM Pacific Time | Pacific timezone |

### Unsupported Format (Limitation)

| Input | Issue | Reason |
|-------|-------|--------|
| `14:30 +1 EST` | Only captures "EST", loses "+1" | Regex only matches last group |

## Luxon Timezone Handling

### How Luxon Handles Timezones

```javascript
DateTime.fromObject(
  {
    year: 2024,
    month: 10,
    day: 25,
    hour: 16,
    minute: 0,
  },
  { zone: "EST" }  // Creates datetime in EST timezone
);
```

This creates a DateTime object that:
- Represents 4:00 PM in Eastern Time
- Internally stores the absolute timestamp
- Can be converted to any other timezone

### Example Flow

**Input:** `"16:00 EST"`

1. **Parse:** Split into `["16:00", undefined, "EST"]`
2. **Extract:** `hours = 16`, `minutes = 0`, `timezone = "EST"`
3. **Create DateTime:** Use base date (flight date) but set time in EST
4. **Result:** A Luxon DateTime representing "today at 4:00 PM EST"

**Input:** `"16:00 +1"`

1. **Parse:** Split into `["16:00", "+1", undefined]`
2. **Extract:** `hours = 16`, `minutes = 0`, `deltaDays = "+1"`
3. **Create DateTime:** Use base date, set time locally, add 1 day
4. **Result:** A Luxon DateTime representing "tomorrow at 4:00 PM local time"

## Timezone Support in Aviation Context

### Why Timezones Matter for Flights

Aviation operations commonly deal with multiple timezones:

- **Departure time:** Local time at departure airport
- **Arrival time:** Local time at arrival airport
- **Flight logs:** Often in UTC/Zulu time
- **Coordination:** Different locations, different timezones

### Common Aviation Timezones

| Code | Timezone | Use Case |
|------|----------|----------|
| `UTC` / `ZULU` | Coordinated Universal Time | Standard for flight operations |
| `EST` / `EDT` | Eastern Time | US East Coast airports |
| `PST` / `PDT` | Pacific Time | US West Coast airports |
| `GMT` | Greenwich Mean Time | UK/Europe |
| `CET` | Central European Time | Continental Europe |

### Example Flight Scenario

**Flight from JFK (EST) to LAX (PST):**

```
Departure: 14:30 EST   (New York local time)
Arrival:   17:45 PST   (Los Angeles local time)
Flight time: ~6 hours (accounting for timezone change)
```

Without timezone support, users would need to:
1. Calculate timezone offsets manually
2. Convert everything to UTC first
3. Risk data entry errors

**With timezone support:**
```
User types: "14:30 EST" for departure
User types: "17:45 PST" for arrival
System handles conversion automatically
```

## Implementation Differences: 16.0 vs Proposed 18.0

### 16.0 Architecture
```
User types "16:00 EST"
    ↓
RelativeDateTimePicker.parseValue()
    ↓
Luxon DateTime.fromObject({ hour: 16, minute: 0 }, { zone: "EST" })
    ↓
Stored as proper timezone-aware DateTime
```

### Proposed 18.0 Architecture (With Timezone)
```
User types "16:00 EST" in input field
    ↓
FlightEventTimeMatrixCell.parseRelativeTime()
    ↓
Custom parsing logic
    ↓
Luxon DateTime.fromObject({ hour: 16, minute: 0 }, { zone: "EST" })
    ↓
Call props.onUpdate() with timezone-aware DateTime
```

## Should We Support Timezones in 18.0?

### Arguments FOR Timezone Support

✅ **Aviation Industry Standard**
- Pilots and flight operations staff work with multiple timezones
- Critical for accurate flight logging

✅ **Data Accuracy**
- Prevents timezone conversion errors
- Preserves original timezone information

✅ **User Convenience**
- Fast data entry: "16:00 EST" instead of mental math
- Matches how aviation professionals think

✅ **Already Implemented in 16.0**
- Users may expect this functionality
- Migration would lose capability

### Arguments AGAINST Timezone Support

❌ **Complexity**
- More parsing logic to maintain
- Edge cases (DST, invalid zones, etc.)
- Need to validate timezone codes

❌ **Timezone Ambiguity**
- "EST" could mean different things (standard vs daylight)
- Some codes are ambiguous
- IANA zones (like "America/New_York") are verbose

❌ **Alternative: Global Timezone Setting**
- Could set timezone at flight level
- All times interpreted in that zone
- Simpler UX, less error-prone

❌ **Luxon Timezone Database**
- Requires timezone data to be loaded
- Adds bundle size
- Not all timezone codes universally supported

## Recommended Approach for 18.0

### Phase 1: Basic Implementation (MVP)
**Support:** Time entry with day offset only
```
"14:30"     → Today at 2:30 PM
"14:30 +1"  → Tomorrow at 2:30 PM
"08:00 -1"  → Yesterday at 8:00 AM
```

**Advantages:**
- Solves 90% of use cases
- Simple, robust parsing
- Easy to test
- Fast to implement

### Phase 2: Add Timezone Support (Enhancement)
**Support:** Time entry with timezone OR day offset
```
"14:30"          → Today at 2:30 PM local
"14:30 +1"       → Tomorrow at 2:30 PM local
"16:00 EST"      → Today at 4:00 PM Eastern
"09:30 UTC"      → Today at 9:30 AM UTC
```

**Requirements:**
1. Validate timezone codes against Luxon's supported zones
2. Show error for invalid timezones
3. Display timezone in formatted output
4. Handle DST transitions gracefully

### Phase 3: Advanced (Future)
**Support:** Combined day offset and timezone
```
"14:30 +1 EST"   → Tomorrow at 2:30 PM Eastern
```

**Requires:**
- More sophisticated regex
- Precedence rules (which comes first?)
- More complex parsing logic

## Implementation: Timezone-Aware Parsing

### Updated Regex Pattern

```javascript
// Match: HH:mm [+/-D] [TIMEZONE]
const REGEX = /^(\d{1,2}):(\d{2})(?:\s+([+-]\d+))?(?:\s+([A-Z]{2,5}))?$/;

// Examples:
// "14:30"           → ["14:30", "14", "30", undefined, undefined]
// "14:30 +1"        → ["14:30 +1", "14", "30", "+1", undefined]
// "16:00 EST"       → ["16:00 EST", "16", "00", undefined, "EST"]
// "14:30 +1 EST"    → ["14:30 +1 EST", "14", "30", "+1", "EST"]
```

### Updated parseRelativeTime Method

```javascript
parseRelativeTime(inputValue) {
  const match = inputValue.match(/^(\d{1,2}):(\d{2})(?:\s+([+-]\d+))?(?:\s+([A-Z]{2,5}))?$/);

  if (!match) {
    return null;  // Invalid format
  }

  const [, hours, minutes, dayOffset, timezone] = match;

  // Validate time values
  const h = parseInt(hours);
  const m = parseInt(minutes);
  if (h < 0 || h > 23 || m < 0 || m > 59) {
    return null;
  }

  let date = this.props.date || DateTime.local();

  // Create datetime with timezone if specified
  if (timezone) {
    try {
      date = DateTime.fromObject(
        {
          year: date.year,
          month: date.month,
          day: date.day,
          hour: h,
          minute: m,
          second: 0,
          millisecond: 0,
        },
        { zone: timezone }
      );

      // Check if timezone is valid
      if (!date.isValid) {
        console.warn(`Invalid timezone: ${timezone}`);
        return null;
      }
    } catch (error) {
      console.error(`Error parsing timezone ${timezone}:`, error);
      return null;
    }
  } else {
    // No timezone - use local
    date = date.set({
      hour: h,
      minute: m,
      second: 0,
      millisecond: 0,
    });
  }

  // Apply day offset if specified
  if (dayOffset) {
    date = date.plus({ days: parseInt(dayOffset) });
  }

  return date.isValid ? date : null;
}
```

### Display Formatted Value with Timezone

```javascript
getFormattedValue() {
  const value = this.props.value;

  if (!value || value === false) {
    return "-";
  }

  try {
    let formatted = formatDateTime(value, { format: "HH:mm" });

    // Add day offset if different from base date
    if (this.props.date && value) {
      const dayDiff = Math.floor(
        value.startOf("day").diff(this.props.date.startOf("day"), "days").days
      );
      if (dayDiff !== 0) {
        formatted += ` ${dayDiff > 0 ? "+" : ""}${dayDiff}`;
      }
    }

    // Add timezone abbreviation if not local
    if (value.zoneName && value.zoneName !== DateTime.local().zoneName) {
      formatted += ` ${value.offsetNameShort}`;  // e.g., "EST", "PST"
    }

    return formatted;
  } catch (error) {
    return "-";
  }
}
```

## Testing Checklist for Timezone Support

### Basic Time Parsing
- [ ] `"14:30"` → Today at 2:30 PM local
- [ ] `"09:00"` → Today at 9:00 AM local
- [ ] `"23:45"` → Today at 11:45 PM local
- [ ] `"00:15"` → Today at 12:15 AM local

### Day Offset Parsing
- [ ] `"14:30 +1"` → Tomorrow at 2:30 PM
- [ ] `"08:00 -1"` → Yesterday at 8:00 AM
- [ ] `"16:00 +2"` → Day after tomorrow at 4:00 PM
- [ ] `"12:00 -3"` → 3 days ago at noon

### Timezone Parsing
- [ ] `"16:00 EST"` → Today at 4:00 PM Eastern
- [ ] `"09:30 UTC"` → Today at 9:30 AM UTC
- [ ] `"14:00 PST"` → Today at 2:00 PM Pacific
- [ ] `"11:00 GMT"` → Today at 11:00 AM GMT

### Combined Parsing
- [ ] `"14:30 +1 EST"` → Tomorrow at 2:30 PM Eastern
- [ ] `"08:00 -1 UTC"` → Yesterday at 8:00 AM UTC

### Invalid Input Handling
- [ ] `"25:00"` → Invalid (hour > 23)
- [ ] `"14:60"` → Invalid (minute > 59)
- [ ] `"14:30 XYZ"` → Invalid (unknown timezone)
- [ ] `"abc:def"` → Invalid (not numbers)
- [ ] `"14"` → Invalid (missing minutes)

### Display Formatting
- [ ] Local time displays without timezone
- [ ] Timezone-aware times show timezone abbreviation
- [ ] Day offsets shown as "+1", "-1", etc.
- [ ] Combined offsets: "14:30 +1 EST"

## Conclusion

**The 16.0 implementation had timezone support, but with limitations:**
- Could only parse timezone OR day offset, not both
- Used a simple regex split
- Relied on Luxon's built-in timezone handling
- Practical for most aviation use cases

**For 18.0, we should:**
1. **Phase 1:** Implement day offset support (high priority, simple)
2. **Phase 2:** Add timezone support if needed by users (medium priority)
3. **Phase 3:** Support combined offset+timezone (low priority, edge case)

**Key Decision Point:** Ask users if they actually use timezone input in 16.0
- If YES → Implement timezone support in Phase 2
- If NO → Focus on day offset and consider flight-level timezone setting instead
