# Flight JSON Widget

Enhanced JSON field widget with pretty formatting for Odoo 18 backend.

## Overview

Provides a custom Odoo widget for displaying JSON fields with syntax highlighting and proper formatting in the backend interface. Makes JSON data readable and easier to work with.

## Features

- **Pretty Formatting**: Automatically formats JSON with proper indentation
- **Syntax Highlighting**: Color-coded JSON elements for readability
- **Backend Widget**: Works in Odoo backend forms and views
- **Easy Integration**: Simply add widget="flight_json" to JSON fields

## Installation

1. Install from Odoo Apps menu
2. Requires: `web` module
3. Widget is automatically available after installation

## Usage

### In Your Models

Add the widget to any JSON or Text field in your XML views:

```xml
<field name="json_data" widget="flight_json" />
```

### Viewing JSON Data

- JSON fields with the widget display formatted and highlighted
- Automatic pretty-printing with indentation
- Color coding for keys, values, and punctuation

## Module Structure

```
flight_json_widget/
└── static/src/
    └── views/fields/flight_json/
        ├── flight_json.js    # Widget JavaScript implementation
        └── flight_json.xml   # Widget template
```

## Use Cases

- **API Data**: Display API responses in readable format
- **Configuration**: Show JSON configuration data
- **Debug Information**: Make debug data easier to read
- **Flight Data**: Display complex flight navigation data (used by flight_plan)

## Technical Details

- **OWL Framework**: Built using Odoo's OWL framework v2
- **ES Modules**: Uses modern JavaScript module system
- **Backend Only**: Designed for backend interface
- **Lightweight**: Minimal dependencies, fast loading

## For Developers

The widget is a standard Odoo field widget that can be applied to any JSON or Text field containing JSON data. It provides automatic formatting without requiring changes to your models.

## Support

- **Author**: Apexive Solutions LLC
- **Website**: https://github.com/smartops-aero/smartops-odoo-flight
- **License**: LGPL-3
