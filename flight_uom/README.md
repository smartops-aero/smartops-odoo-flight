# Flight UOM

Aviation-specific units of measurement for flight operations in Odoo 16.

## Overview

Adds essential aviation units of measurement to Odoo's UOM system. Includes distance units (nautical miles, statute miles) and speed units (knots, kph) with accurate conversion factors following international aviation standards.

## Features

### Distance Units

- **Nautical Miles (nm)**: Standard aviation distance measurement
- **Statute Miles (mi)**: Alternative distance measurement
- **Kilometers (km)**: Metric distance measurement

### Speed Units

- **Knots (kt)**: Standard aviation speed (nautical miles per hour)
- **Kilometers per hour (kph)**: Metric speed measurement
- **Feet per second (fps)**: Vertical speed measurement

## Installation

1. Install from Odoo Apps menu
2. Requires: `uom` module
3. Units are automatically loaded upon installation

## Usage

### Using Aviation Units

1. Units are available in any UOM field throughout Odoo
2. Select from the **Distance** or **Speed** categories
3. Odoo automatically converts between units as needed

### In Flight Modules

Aviation units are used throughout the flight module suite for:

- Flight distances and ranges
- Aircraft speeds and velocities
- Route planning calculations

## Module Structure

```
flight_uom/
└── data/
    └── product_uom_data.xml    # UOM definitions with conversion factors
```

## Conversion Factors

All conversion factors follow international aviation standards:

- 1 nautical mile = 1.852 kilometers
- 1 statute mile = 1.609344 kilometers
- 1 knot = 1 nautical mile per hour
- Accurate conversions for all defined units

## Use Cases

- **Flight Planning**: Calculate distances and fuel requirements
- **Performance Calculations**: Track aircraft speeds in proper units
- **International Operations**: Convert between metric and aviation units
- **Reporting**: Generate reports with standardized aviation measurements

## Technical Details

- **Data Module**: Only contains UOM definitions, no models
- **Categories**: Adds Distance and Speed UOM categories
- **Standards Compliant**: All factors match ICAO/FAA standards
- **System-Wide**: Available across all Odoo modules

## Support

- **Author**: Apexive Solutions LLC
- **Website**: https://github.com/smartops-aero/smartops-odoo-flight
- **License**: LGPL-3
