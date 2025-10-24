# Flight Event Time Matrix Components

## Architecture Overview

The Flight Event Time Matrix is a custom Odoo 18 field widget that displays flight event times in a matrix format. It consists of three interconnected components:

```
FlightEventTimeMatrixField (Main Field Widget)
    └── FlightEventTimeMatrixRenderer (Table Layout)
            └── FlightEventTimeMatrixCell (Individual Cells)
```

## Component Responsibilities

### FlightEventTimeMatrixField

- **Location**: `flight_event_time_matrix_field/`
- **Purpose**: Bridge between Odoo form view and the matrix display
- **Key Responsibilities**:
  - Fetches event codes from `flight.event.code` model
  - Manages One2many field (`flight_event_time_ids`)
  - Handles database operations (create/update records)
  - Provides time kinds (Actual/Scheduled)

### FlightEventTimeMatrixRenderer

- **Location**: `flight_event_time_matrix_renderer/`
- **Purpose**: Manages the table layout and data structure
- **Key Responsibilities**:
  - Converts flat record list to 2D matrix structure
  - Renders table with event codes as rows, time kinds as columns
  - Passes data to individual cell components
  - Propagates cell updates to parent field

### FlightEventTimeMatrixCell

- **Location**: `flight_event_time_matrix_cell/`
- **Purpose**: Individual cell with text input and datetime picker
- **Key Responsibilities**:
  - Provides text input field for keyboard-driven time entry
  - Parses typed input in formats: "HH:mm", "HH:mm +/-D", "HH:mm TZ"
  - Manages its own `useDateTimePicker` hook for visual picker
  - Formats time with relative day offset (e.g., "14:30 +1")
  - Opens datetime picker on Ctrl+Click
  - Uses onApply callback to prevent auto-closing

#### Supported Input Formats

- `14:30` - Same day at 2:30 PM
- `14:30 +1` - Next day at 2:30 PM
- `08:00 -1` - Previous day at 8:00 AM
- `16:00 EST` - Same day at 4:00 PM Eastern Time
- `14:30 +1 UTC` - Next day at 2:30 PM UTC

#### Keyboard Shortcuts

- **Enter** - Parse and apply the typed time
- **Escape** - Revert to previous value
- **Ctrl+Click** - Open visual datetime picker
- **Focus** - Auto-select all text for easy editing

## Data Flow

1. **Form → Field**: Odoo form passes One2many field data to FlightEventTimeMatrixField
2. **Field → Renderer**: Field component passes list, eventCodes, timeKinds, and date
3. **Renderer → Cells**: Renderer creates matrix and passes individual values to cells
4. **Cell → Field**: Cell updates trigger callback chain back to field for DB save

## Known Issues

### Date Update Not Refreshing Matrix

- **Problem**: When flight date changes, matrix doesn't update relative day displays
- **Cause**: `onWillUpdateProps` not triggered for field component when other fields change
- **Workaround**: Manual form refresh or save/reload

### Technical Details

- Field components in Odoo 18 don't automatically receive new props when sibling fields change
- The state.date in FlightEventTimeMatrixField doesn't sync with record.data.date changes
- Potential solutions require deeper integration with Odoo's field update system

## Usage

The widget is registered as `flight_event_time_matrix` and used in views like:

```xml
<field name="flight_event_time_ids" widget="flight_event_time_matrix" />
```

## Dependencies

- `@odoo/owl` - Component framework
- `@web/core/datetime/datetime_hook` - DateTime picker functionality
- `@web/core/l10n/dates` - Date formatting
- `luxon` - DateTime manipulation

## Testing

To test the matrix:

1. Create/edit a flight record
2. Set a flight date
3. Click on matrix cells to add event times
4. Verify relative day calculations update correctly
5. Check that Apply/Close buttons work without auto-closing
