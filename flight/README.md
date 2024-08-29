# Flight Management Module

## Overview

The Flight Management module is a base module for managing flights, aircraft, and aerodromes in Odoo. It provides basic models and views that can be extended by other modules for more advanced functionality.

## Features

- Management of flights
- Aircraft tracking
- Aerodrome (airport) information
- Integration with Odoo's mail and activity features

## Installation

1. Clone this repository or download the module.
2. Place the `flight` folder in your Odoo addons directory.
3. Update the apps list in your Odoo instance.
4. Install the "Flight" module from the Apps menu.

## Configuration

### Aerodrome Data

Due to the large size of the aerodrome data, it is not loaded by default. To load the data:

1. Download the CSV file from [this link](https://raw.githubusercontent.com/smartops-aero/smartops-odoo-flight/16.0/flight/data/flight.aerodrome.csv).
2. Go to Flights -> Configuration -> Aerodromes.
3. Click on "Favorites" and select "Import records".
4. Upload the downloaded CSV file.

## Usage

After installation, you can access the flight management features from the "Flights" menu in the main Odoo navigation.

## Models

- `flight.flight`: Represents individual flights
- `flight.aircraft`: Stores aircraft information
- `flight.aerodrome`: Contains airport data
- `flight.aircraft.class`: Defines aircraft categories and classes
- `flight.aircraft.make`: Stores aircraft manufacturers
- `flight.aircraft.model`: Represents specific aircraft models

## Views

The module provides tree, form, and search views for flights, aircraft, and aerodromes.

## Extending the Module

This base module is designed to be extended. See the Flight Events (`flight_event`) and Flight Operations Management (`flight_ops`) modules for an example of how to add more advanced functionality.

## Support

For questions or support, please contact the module maintainer or open an issue on the GitHub repository.

## License

This module is licensed under LGPL-3.
