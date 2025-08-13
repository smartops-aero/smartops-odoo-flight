# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Odoo 18.0 module suite for aviation/flight management called SmartOps Flight. It provides comprehensive functionality for managing flights, aircraft, aerodromes, crew, and related aviation operations.

**Note:** Recently migrated from Odoo 16.0 to 18.0. See MIGRATION_16_TO_18.md for details.

## Module Architecture

The codebase consists of multiple interdependent Odoo modules:

- **flight**: Core module with base models for flights, aircraft, aerodromes, and crew
- **flight_aircraft_spec**: Aircraft specifications and amenities management
- **flight_data_sync**: Data synchronization with external providers
- **flight_event**: Flight events and phases tracking (takeoff, landing, etc.)
- **flight_number**: Flight number management and prefix configuration
- **flight_portal**: Portal access for external users
- **flight_uom**: Aviation-specific units of measurement
- **website_flight_fleet**: Public website features for fleet display

### Module Dependencies

Modules inherit from `flight` base module and follow Odoo's dependency chain. The `flight_uom` module provides units of measurement used across other modules.

## Development Commands

### Code Quality and Formatting

```bash
# Run pre-commit hooks (includes ruff, prettier, eslint, and Odoo-specific checks)
pre-commit run --all-files

# Run ruff for Python linting and formatting
ruff check . --fix
ruff format .

# Run eslint for JavaScript
npx eslint . --fix

# Run prettier for XML, HTML, CSS, and JS formatting
npx prettier --write "**/*.{xml,html,css,js,json,yml}"
```

### Odoo Development

```bash
# Start Odoo with this module path
# Note: Assumes Odoo is installed and configured
odoo -c odoo.conf --addons-path=/Users/alexis/Work/kzr/kzr-odoo/extra-addons/.src/smartops/flight,/path/to/odoo/addons

# Update module list and install/upgrade modules
odoo -c odoo.conf -u flight -i flight_event,flight_aircraft_spec

# Run Odoo in development mode with auto-reload
odoo -c odoo.conf --dev=reload
```

### Testing

```bash
# Run tests for a specific module
odoo -c odoo.conf --test-enable --stop-after-init -u flight

# Run tests with coverage
coverage run odoo -c odoo.conf --test-enable --stop-after-init -u flight
coverage report
```

## Key Technical Patterns

### Model Structure

All flight-related models inherit from:

- `mail.thread` - for chatter and activity tracking
- `mail.activity.mixin` - for scheduled activities
- `flight.lock.mixin` - custom mixin for record locking functionality

### Security Model

- Uses Odoo's standard access control with `ir.model.access.csv` files
- Security groups defined in `security/security.xml`
- Portal users have limited read access via `flight_portal` module

### Frontend Components

- Custom Odoo 18 widgets in `static/src/components/`
- Uses OWL framework v2 for reactive components
- JavaScript modules use ES module format with `/** @odoo-module **/`
- JavaScript assets registered in `__manifest__.py` under `assets` key

### Data Management

- CSV data files for initial setup in `data/` directories
- XML demo data in `demo/` directories
- Large aerodrome dataset loaded separately due to size

### Migration Handling

- Version-specific migrations in `migrations/` folders
- Follow pattern: `migrations/{version}/post-migrate.py` or `pre-migrate.py`

## Important Considerations

### Aerodrome Data

The full aerodrome dataset is not included by default. To load:

1. Download from: https://raw.githubusercontent.com/smartops-aero/smartops-odoo-flight/18.0/flight/data/flight.aerodrome.csv
2. Import via Flights -> Configuration -> Aerodromes -> Import

### Build System

Uses `whool` build backend (specified in `pyproject.toml`) for Python package management.

### Python Requirements

- Python 3.10+ (recommended 3.11+)
- See requirements.txt for any external dependencies

### Code Style

- Python: Ruff with custom configuration (target Python 3.11+)
- JavaScript: ESLint with Odoo-specific globals, ES modules with `/** @odoo-module **/`
- XML/HTML: Prettier with XML plugin
- Pre-commit hooks enforce all style rules

### Branch Strategy

- Main branch: `18.0` (Odoo version)
- Previous version: `16.0` branch
- All PRs should target the `18.0` branch

## Common Troubleshooting

1. **Module not found**: Ensure the addons path includes this directory
2. **Access rights errors**: Check `ir.model.access.csv` for missing entries
3. **JavaScript errors**: Verify asset bundle registration in `__manifest__.py`
4. **Migration issues**: Check version numbers in `__manifest__.py` match migration folders
