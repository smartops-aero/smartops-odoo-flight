# Flight Event Module

## Overview

The Flight Event module is an extension for the Flight Management system in Odoo. 
It provides functionality for tracking flight events, phases and durations, enhancing the capabilities of flight operations management.

## Features

- Track flight events (e.g., takeoff, landing) with precise timestamps
- Define and manage flight phases
- Flexible time input system with timezone and relative day support
- Integration with the base Flight module

## Installation

1. Ensure that the base `flight` module is installed.
2. Place the `flight_event` folder in your Odoo addons directory.
3. Update the apps list in your Odoo instance.
4. Install the "Flight Events" module from the Apps menu.

## Configuration

After installation, you can configure flight event codes and phases from the Flight Configuration menu.

## Usage

### Time Input

The Flight Event module uses a sophisticated time input system:

- Times are displayed in the user's time zone but stored as UTC in the database.
- The input widget accepts times with additional timezone information. For example:
    - `10:00 UTC` will be converted from UTC to your local time zone.
- You can enter times relative to the flight date using the `+` or `-` notation:
    - `10:00+1` means 10:00 AM on the day after the flight date.
    - `23:00-1` means 11:00 PM on the day before the flight date.
- Combining relative days and timezones is also possible:
    - `10:00+1 UTC` means 10:00 AM UTC on the day after the flight date.

This flexible system allows for precise and convenient time entry across different time zones and flight schedules.

### Recording Flight Events

1. Navigate to a flight record.
2. In the "Times" tab, you'll see a matrix of event times.
3. Enter the times for various events using the format described above.
4. The system will automatically calculate flight phases based on these events.
5. View the calculated phase durations in the "Phase Durations" tab.

## Models

- `flight.event.time`: Stores individual event times for flights
- `flight.event.code`: Defines types of flight events (e.g., takeoff, landing)
- `flight.phase`: Defines flight phases (e.g., block, flight, taxi-in, taxi-out, cruise etc)
- `flight.phase.duration`: Computed durations of flight phases

## Views

The module adds new views to the flight form, including a matrix view for easily entering and viewing flight event times.

## Key Features

### Event Sequence Constraint

The module enforces a constraint to ensure that event times are in the correct sequence for each time kind. This helps maintain data integrity and prevents logical errors in event recording.

### Dynamic Event Time Matrix

A custom widget (`FlightEventTimeMatrixField`) provides an intuitive interface for entering and viewing event times. It dynamically fetches time kinds and event codes, making it flexible and easy to use.

### Automatic Phase Duration Calculation

Phase durations are automatically calculated based on the recorded event times. This eliminates manual calculations and ensures accuracy.

## Technical Notes

- The module uses computed fields and constraints to ensure data consistency.
- Custom JavaScript widgets are used for the event time matrix interface.

## Extending the Module

This module is designed to be extensible. You can create custom event types, phases, or additional computations based on flight events.

## Support

For questions or support, please contact the module maintainer or open an issue on the GitHub repository.

## License

This module is licensed under LGPL-3.
