# Flight Aircraft Specifications

Comprehensive aircraft specifications management system for Odoo 18.

## Overview

Manage aircraft specifications with flexible categorization and multiple value types. Replaces the previous `flight_aircraft_specifications` and `flight_aircraft_amenities` modules with a unified approach.

## Features

- **Spec Categories**: Organize specifications (Cabin Features, Entertainment, Connectivity, Dimensions)
- **Flexible Value Types**: Boolean, Text, and Float values with automatic UOM handling
- **Aircraft Association**: Link specs directly to individual aircraft
- **Seat Maps**: Store seat configuration images
- **Translatable**: Multi-language support for names and descriptions
- **Change Tracking**: Built-in chatter integration for tracking modifications

## Installation

1. Install from Odoo Apps menu
2. Requires: `base`, `flight`, `uom` modules

## Usage

### Setup Specifications

1. Go to **Flights → Configuration → Spec Categories**
2. Create categories (e.g., "Connectivity", "Dimensions")
3. Go to **Flights → Configuration → Spec Codes**
4. Define specification codes with value types and optional UOM

### Apply to Aircraft

1. Open any **Aircraft** record
2. Navigate to the **Specifications** tab
3. Add specifications and set values
4. Optionally upload a seat map image

## Module Structure

```
flight_aircraft_spec/
├── models/
│   ├── flight_aircraft.py              # Extends aircraft model
│   ├── flight_aircraft_spec.py         # Spec values on aircraft
│   ├── flight_aircraft_spec_category.py # Spec categories
│   └── flight_aircraft_spec_code.py     # Spec definitions
├── views/
│   ├── flight_aircraft_views.xml       # Aircraft form enhancements
│   └── flight_aircraft_spec_views.xml  # Spec management views
└── data/
    └── flight_aircraft_spec_data.xml   # Default categories/codes
```

## Example Use Cases

- **Charter Operations**: Track WiFi, entertainment, and amenities for client matching
- **Fleet Management**: Maintain detailed aircraft capability records
- **Maintenance Planning**: Store technical specifications and dimensions

## Technical Details

- **Value Types**: Boolean (yes/no), Text (descriptions), Float (measurements with UOM)
- **Dependencies**: Integrates with `uom` module for measurement conversions
- **Extensible**: Add custom spec codes without code changes

## Support

- **Author**: Apexive Solutions LLC
- **Website**: https://github.com/smartops-aero/smartops-odoo-flight
- **License**: LGPL-3
