# Flight Event Time Matrix - Issues & Solutions

## Issues Identified

### Issue 1: Cannot Enter Times Until Flight is Saved
**Problem:** When creating a new flight, the time matrix cells are not editable until the parent flight record is saved.

**Root Cause:** The `flight_event_time_ids` is a One2many field that requires a parent record ID to create related records. The `commitChange` method tries to create records with:
```javascript
flight_id: this.props.record.id || this.props.record.resId
```
Both values are `null/undefined` for unsaved records.

**Impact:** Poor UX - users must save an incomplete flight record before adding event times.

---

### Issue 2: No Typed Time Entry with Relative Day Offset
**Problem:** Odoo 18 version removed the custom `RelativeDateTimePicker` that allowed typed input like "14:30 +1" or "16:00 EST".

**What Was Lost:**
- Ability to type time with day offset (e.g., "14:30 +1" for next day)
- Timezone support in input (e.g., "16:00 EST")
- Custom parsing logic for shorthand time entry
- Keyboard-first workflow

**Current Behavior:** Users must:
1. Click cell to open picker popover
2. Use visual date/time picker
3. Click Apply button
4. Much slower than typing

---

## Solution Design

### Solution 1: Enable Time Entry Before Save (X2Many Fields)

Odoo 18 supports **x2many fields in new records** through the `addNewRecord` API, which creates temporary records that are persisted when the parent saves.

**Approach:**
The current code already handles this correctly! The issue is likely in how the field is being used or a missing configuration.

**Required Checks:**
1. Ensure the field widget is in "edit" mode for new records
2. Verify the One2many field is properly configured
3. Check if there are domain/context restrictions

**Potential Fix:**
```javascript
async commitChange(timeKind, eventCode, value) {
  if (!value) return;

  if (!this.list) {
    return;
  }

  const matchingRecords = this.list.records.filter(
    (record) =>
      record.data.time_kind === timeKind.key &&
      record.data.code_id[0] === eventCode.id
  );

  if (matchingRecords.length === 1) {
    await matchingRecords[0].update({ time: value });
  } else if (matchingRecords.length === 0) {
    // Create new record - this works for unsaved parent records in Odoo 18!
    const record = await this.list.addNewRecord({
      mode: "edit",
    });
    const values = {
      time: value,
      time_kind: timeKind.key,
      code_id: [eventCode.id, eventCode.code],
      // flight_id will be set automatically by Odoo when parent saves
      // No need to explicitly set it here
    };
    await record.update(values);
    this.render(); // Force UI update
  }
}
```

---

### Solution 2A: Add Input Field to Cell (Recommended)

Create a **hybrid component** that combines both typed input AND picker functionality.

**Architecture:**
```
FlightEventTimeMatrixCell
├── <input> element for typed entry
└── DateTimePicker popover (on click/Ctrl+Enter)
```

**Key Features:**
1. Always show an input field in each cell
2. Allow typing relative time format: "HH:mm [+/-D]" (e.g., "14:30 +1")
3. Click input or press Ctrl+Enter to open visual picker
4. Parse custom format on blur/enter
5. Display formatted value with relative day offset

**Implementation Strategy:**

```javascript
// In FlightEventTimeMatrixCell component

setup() {
  this.inputRef = useRef("time-input");

  // Use the datetimepicker service with input element
  const dateTimePicker = useDateTimePicker({
    target: this.inputRef,
    get pickerProps() {
      return {
        value: props.value || props.date || DateTime.local(),
        type: "datetime",
      };
    },
    format: "HH:mm",  // Base format without day offset
    onApply: (value) => {
      if (value) {
        props.onUpdate(props.timeKind, props.eventCode, value);
      }
    },
  });

  this.openPicker = dateTimePicker.open;
}

// Custom parsing method
parseRelativeTime(inputValue) {
  // Match patterns:
  // - "14:30" (same day)
  // - "14:30 +1" (next day)
  // - "14:30 -1" (previous day)
  // - "14:30 EST" (with timezone)

  const match = inputValue.match(/^(\d{1,2}):(\d{2})\s*([+-]?\d+)?\s*([A-Z]{3,4})?$/);

  if (!match) {
    return null;  // Invalid format
  }

  const [, hours, minutes, dayOffset, timezone] = match;
  let date = this.props.date || DateTime.local();

  if (timezone) {
    date = DateTime.fromObject(
      {
        year: date.year,
        month: date.month,
        day: date.day,
        hour: parseInt(hours),
        minute: parseInt(minutes),
      },
      { zone: timezone }
    );
  } else {
    date = date.set({
      hour: parseInt(hours),
      minute: parseInt(minutes),
      second: 0,
      millisecond: 0,
    });
  }

  if (dayOffset) {
    date = date.plus({ days: parseInt(dayOffset) });
  }

  return date;
}

// Event handlers
onInputBlur(ev) {
  const parsed = this.parseRelativeTime(ev.target.value);
  if (parsed && parsed.isValid) {
    this.props.onUpdate(this.props.timeKind, this.props.eventCode, parsed);
  }
}

onInputKeydown(ev) {
  if (ev.key === "Enter") {
    ev.preventDefault();
    const parsed = this.parseRelativeTime(ev.target.value);
    if (parsed && parsed.isValid) {
      this.props.onUpdate(this.props.timeKind, this.props.eventCode, parsed);
    }
  } else if (ev.key === "Enter" && ev.ctrlKey) {
    // Open picker on Ctrl+Enter
    ev.preventDefault();
    this.openPicker(0);
  }
}
```

**Template:**
```xml
<t t-name="flight_event.FlightEventTimeMatrixCell">
  <input
    t-ref="time-input"
    type="text"
    class="o_matrix_cell_input form-control form-control-sm"
    t-att-value="getFormattedValue()"
    t-att-readonly="props.readonly"
    t-on-blur="onInputBlur"
    t-on-keydown="onInputKeydown"
    t-on-click="onClick"
    placeholder="HH:mm"
    title="Enter time (format: HH:mm or HH:mm +1 for next day)"
  />
</t>
```

**Advantages:**
- Fast keyboard entry
- Visual picker still available
- Familiar 16.0 behavior restored
- Best UX

---

### Solution 2B: Custom DateTimePicker Component (Alternative)

Port the 16.0 `RelativeDateTimePicker` to work with Odoo 18's new architecture.

**Challenge:** Odoo 18 completely changed the datetime picker implementation:
- 16.0: Class-based components extending `DateTimePicker`
- 18.0: Hook-based with service layer (`useDateTimePicker` + `datetimepicker_service`)

**Approach:**
Create a custom hook that wraps `useDateTimePicker` but adds custom parsing:

```javascript
export function useRelativeDateTimePicker(hookParams) {
  const baseDate = hookParams.baseDate;

  // Wrap the format parameter to add custom parsing
  const originalFormat = hookParams.format;
  const customFormat = originalFormat || "HH:mm";

  // Create custom parser wrapper
  const wrappedHookParams = {
    ...hookParams,
    format: customFormat,
    // Intercept the value before it goes to the service
    pickerProps: {
      ...hookParams.pickerProps,
      get value() {
        // Custom logic here if needed
        return hookParams.pickerProps.value;
      },
    },
  };

  // Use the base hook
  const { state, open } = useDateTimePicker(wrappedHookParams);

  // Add custom parsing function
  const parseRelativeTime = (inputString) => {
    // Same parsing logic as Solution 2A
    // ...
  };

  return { state, open, parseRelativeTime };
}
```

**Disadvantages:**
- More complex
- May break with Odoo updates
- Requires deep understanding of datetime picker internals

---

## Recommended Implementation Plan

### Phase 1: Fix Issue #1 (Time Entry Before Save) - IMMEDIATE

**Steps:**
1. Test if `addNewRecord` works for unsaved parent records
2. If not, check for field configuration issues
3. Verify the view XML configuration
4. Add defensive checks for readonly states
5. Test thoroughly with new flight creation

**Expected Outcome:** Users can add event times immediately after setting flight date, even before saving.

---

### Phase 2: Implement Typed Time Entry - HIGH PRIORITY

**Recommended: Solution 2A (Input Field Approach)**

**Implementation Steps:**

1. **Update FlightEventTimeMatrixCell component:**
   - Replace `<span>` with `<input>` element
   - Add `useRef` for input
   - Integrate `useDateTimePicker` with input ref
   - Implement `parseRelativeTime()` method
   - Add blur/keydown event handlers

2. **Update template:**
   - Change from span to input element
   - Add proper CSS classes
   - Add placeholder and title attributes
   - Keep click handler for picker

3. **Update CSS:**
   - Style input field to look clean in table
   - Remove padding when readonly
   - Add focus states

4. **Test cases:**
   - "14:30" → Same day at 2:30 PM
   - "14:30 +1" → Next day at 2:30 PM
   - "08:00 -1" → Previous day at 8:00 AM
   - "16:00 EST" → Same day at 4:00 PM EST (stretch goal)
   - Invalid inputs → Keep existing value
   - Click input → Open visual picker
   - Ctrl+Enter → Open visual picker

---

## Code Changes Required

### File 1: `flight_event_time_matrix_cell.js`

**Changes:**
1. Add input ref
2. Add parseRelativeTime method
3. Add onInputBlur handler
4. Add onInputKeydown handler
5. Update onClick to work with input
6. Integrate useDateTimePicker with input element

### File 2: `flight_event_time_matrix_cell.xml`

**Changes:**
1. Replace `<span>` with `<input>`
2. Add event handlers
3. Add ref attribute
4. Update classes

### File 3: `flight_event_time_matrix.scss`

**Changes:**
1. Add styles for input field
2. Ensure proper alignment in table cells
3. Add focus states
4. Handle readonly state styling

---

## Expected Benefits

### For Issue #1:
- ✅ Improved workflow - no need to save incomplete records
- ✅ Better UX - immediate feedback
- ✅ Aligned with Odoo 18 best practices

### For Issue #2:
- ✅ Fast keyboard-driven time entry restored
- ✅ Relative day offset support ("14:30 +1")
- ✅ Visual picker still available for mouse users
- ✅ Familiar workflow from 16.0
- ✅ Reduced clicks - type instead of point-and-click

---

## Migration Path from 16.0

### What's Different:
| Feature | 16.0 | 18.0 (Proposed) |
|---------|------|-----------------|
| **Input Method** | RelativeDateTimePicker component | Input field with useDateTimePicker hook |
| **Typed Entry** | Yes (HH:mm [+/-D]) | Yes (same format) |
| **Visual Picker** | Bootstrap DateTimePicker | Odoo 18 native picker |
| **Timezone Support** | Yes (EST, PST, etc.) | Possible (stretch goal) |
| **Component Architecture** | Extended DateTimePicker class | Hook-based with input element |
| **Before Save Entry** | Unknown | Yes (supported) |

### What's Better in 18.0:
- Native Odoo 18 integration
- More maintainable code
- Better mobile support
- Follows Odoo patterns

### What Requires Adaptation:
- Custom parsing moved to component level
- Different event handling
- New CSS for input styling

---

## Testing Checklist

### Issue #1 Tests:
- [ ] Create new flight without saving
- [ ] Set flight date
- [ ] Click matrix cell
- [ ] Verify picker opens
- [ ] Select time
- [ ] Verify time appears in matrix
- [ ] Save flight
- [ ] Verify times are persisted correctly

### Issue #2 Tests:
- [ ] Type "14:30" and press Enter → Same day, 2:30 PM
- [ ] Type "14:30 +1" → Next day, 2:30 PM
- [ ] Type "08:00 -1" → Previous day, 8:00 AM
- [ ] Type "23:45 +0" → Same day, 11:45 PM
- [ ] Type invalid format → No change
- [ ] Click input → Picker opens
- [ ] Use picker to select time → Updates correctly
- [ ] Test readonly mode → Input disabled
- [ ] Test with empty cell → Placeholder shown

---

## Implementation Timeline

**Estimated Effort:**

| Task | Complexity | Time | Priority |
|------|-----------|------|----------|
| Issue #1: Fix before-save entry | Low | 2-4 hours | High |
| Issue #2: Design & prototype | Medium | 4-6 hours | High |
| Issue #2: Implement input field | Medium | 6-8 hours | High |
| Issue #2: Add parsing logic | Medium | 4-6 hours | High |
| Issue #2: CSS styling | Low | 2-3 hours | Medium |
| Issue #2: Testing & refinement | Medium | 4-6 hours | High |
| **Total** | | **22-33 hours** | |

---

## Next Steps

1. **Validate Issue #1:** Test if the current code actually works for unsaved records
2. **Prototype Solution 2A:** Create a minimal input-based cell
3. **Get user feedback:** Confirm the desired behavior
4. **Implement:** Follow the implementation plan above
5. **Test:** Run through all test cases
6. **Document:** Update component README with new features

---

## Questions to Resolve

1. **Timezone support:** Do we need timezone input support (like "16:00 EST")?
   - If yes: More complex parsing required
   - If no: Simpler implementation

2. **Date picker access:** Should clicking the input open the picker or only Ctrl+Enter?
   - Input click: Better for mouse users
   - Ctrl+Enter only: Better for keyboard users
   - **Recommendation:** Both

3. **Invalid input handling:** What happens when user types invalid time?
   - Keep existing value?
   - Clear the field?
   - Show error message?
   - **Recommendation:** Keep existing value, show brief error notification

4. **Format documentation:** Should we show format hint in UI?
   - Tooltip on hover?
   - Placeholder text?
   - Help text below table?
   - **Recommendation:** Tooltip + placeholder

---

## References

- **Odoo 18 useDateTimePicker hook:** `/src/odoo/addons/web/static/src/core/datetime/datetime_hook.js`
- **Odoo 18 DateTimePicker component:** `/src/odoo/addons/web/static/src/core/datetime/datetime_picker.js`
- **Odoo 18 DateTimePicker service:** `/src/odoo/addons/web/static/src/core/datetime/datetimepicker_service.js`
- **16.0 RelativeDateTimePicker:** `@flight_event/static/src/flight_event_16.0_backup/components/relative_datetimepicker/`
