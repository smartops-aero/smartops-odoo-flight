# SmartOps Flight

A comprehensive Odoo 18.0 module suite for aviation and flight management operations.

## Overview

SmartOps Flight provides end-to-end functionality for managing flights, aircraft, crew, aerodromes, and related aviation operations. The suite is designed for airlines, charter operators, and aviation service providers.

## Modules

### Core Modules
- **flight** - Base models for flights, aircraft, aerodromes, and crew
- **flight_event** - Flight events and phases tracking (takeoff, landing, delays)
- **flight_plan** - Flight plan routes, waypoints, and aerodrome management
- **flight_uom** - Aviation-specific units of measurement

### Specialized Modules  
- **flight_aircraft_spec** - Aircraft specifications and amenities management
- **flight_data_sync** - Data synchronization with external aviation providers
- **flight_number** - Flight number management and prefix configuration
- **flight_portal** - Portal access for external users and stakeholders
- **website_flight_fleet** - Public website features for fleet display

## Key Features

- **Flight Management** - Complete flight lifecycle from planning to completion
- **Aircraft Tracking** - Aircraft specifications, maintenance, and utilization
- **Crew Management** - Pilot and cabin crew scheduling and qualifications
- **Route Planning** - Waypoint-based flight routes with coordinate validation
- **Event Tracking** - Real-time flight phase monitoring and reporting
- **Portal Integration** - External user access for flight information
- **Website Integration** - Public fleet showcase and aircraft information

## Installation

1. Clone the repository to your Odoo addons path
2. Install the base `flight` module through Odoo Apps
3. Install additional modules as needed for your use case

## Requirements

- Odoo 18.0+
- Python 3.11+
- PostgreSQL (recommended for production)

## Documentation

- [Migration Guide](MIGRATION_16_TO_18.md) - Odoo 16.0 to 18.0 migration details
- [Testing Guide](TESTING.md) - Comprehensive testing documentation
- [Development Guide](CLAUDE.md) - Development patterns and commands

## License

LGPL-3

## Support

For technical support and custom development, contact Apexive Solutions LLC.