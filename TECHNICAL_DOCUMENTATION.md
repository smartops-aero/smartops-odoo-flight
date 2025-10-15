# SmartOps Flight - Technical Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Module Structure](#module-structure)
4. [Core Modules](#core-modules)
5. [Data Models](#data-models)
6. [Security Model](#security-model)
7. [API Reference](#api-reference)
8. [Frontend Components](#frontend-components)
9. [Installation & Deployment](#installation--deployment)
10. [Development Guidelines](#development-guidelines)

## Overview

SmartOps Flight is a comprehensive Odoo 18.0 module suite designed for aviation and flight management. It provides enterprise-grade functionality for managing flights, aircraft, aerodromes, crew members, and related aviation operations.

### Key Features

- Complete flight operations management
- Aircraft fleet tracking and specifications
- Aerodrome database with ICAO/IATA codes
- Crew management and assignment
- Flight event tracking and phase management
- Portal access for external stakeholders
- Public website integration for fleet display
- Aviation-specific units of measurement
- Data synchronization with external providers

### Technology Stack

- **Platform**: Odoo 18.0 Community Edition
- **Python**: 3.11+
- **Frontend**: OWL Framework 2.0 (Odoo Web Library)
- **Database**: PostgreSQL
- **Build System**: Whool (Python package management)

## Architecture

### Module Dependency Graph

```
flight_uom (base units)
    ↓
flight (core module)
    ├── flight_aircraft_spec (specifications)
    ├── flight_event (event tracking)
    ├── flight_number (number management)
    ├── flight_data_sync (external sync)
    ├── flight_portal (portal access)
    └── website_flight_fleet (public website)
```

### Design Patterns

- **Mixin Inheritance**: All models inherit from standard Odoo mixins

  - `mail.thread` - Chatter and messaging
  - `mail.activity.mixin` - Activity scheduling
  - `flight.lock.mixin` - Custom record locking
  - `avatar.mixin` - Avatar management

- **MVC Architecture**: Standard Odoo MVC pattern
  - Models: Business logic and data
  - Views: XML templates and forms
  - Controllers: HTTP request handling

## Module Structure

### Directory Layout

```
smartops/flight/
├── flight/                  # Core module
│   ├── models/             # Data models
│   ├── views/              # UI views
│   ├── security/           # Access control
│   ├── data/               # Initial data
│   ├── demo/               # Demo data
│   ├── static/             # Assets
│   └── tests/              # Unit tests
├── flight_aircraft_spec/    # Aircraft specifications
├── flight_data_sync/        # External sync
├── flight_event/           # Event management
├── flight_number/          # Number management
├── flight_portal/          # Portal access
├── flight_uom/             # Units of measure
└── website_flight_fleet/   # Public website
```

## Core Modules

### 1. Flight (Base Module)

**Purpose**: Core foundation providing base models and functionality

**Key Models**:

- `flight.flight` - Flight records
- `flight.aircraft` - Aircraft registry
- `flight.aerodrome` - Airport database
- `flight.crew` - Crew management

**Features**:

- Flight scheduling and tracking
- Aircraft registration and management
- Aerodrome database (ICAO/IATA)
- Crew assignment and roles
- Lock mechanism for data integrity

### 2. Flight Aircraft Spec

**Purpose**: Detailed aircraft specifications and amenities

**Key Models**:

- `flight.aircraft.spec` - Specification records
- `flight.aircraft.spec.category` - Specification categories
- `flight.aircraft.spec.code` - Specification codes

**Features**:

- Aircraft amenities management
- Specification categorization
- Custom specification codes
- Integration with base aircraft model

### 3. Flight Data Sync

**Purpose**: Synchronization with external data providers

**Key Models**:

- `flight.data.provider` - External provider configuration
- `flight.data.registry` - Sync registry and status

**Features**:

- Configurable data providers
- Scheduled synchronization (cron)
- Sync status tracking
- Error handling and logging
- Wizard for manual sync

### 4. Flight Event

**Purpose**: Flight event tracking and phase management

**Key Models**:

- `flight.event.code` - Event type definitions
- `flight.event.time` - Event timestamps
- `flight.phase` - Flight phases
- `flight.phase.duration` - Phase duration calculation

**Features**:

- Event code management (takeoff, landing, etc.)
- Multiple time types (Actual, Scheduled, Estimated)
- Phase duration tracking
- Event history logging
- Custom OWL components for time matrix display

### 5. Flight Number

**Purpose**: Flight number management and prefix configuration

**Key Models**:

- `flight.number` - Flight number records
- `flight.prefix` - Airline prefix configuration

**Features**:

- Airline prefix management
- Flight number validation
- Automatic number generation
- Integration with flight records

### 6. Flight Portal

**Purpose**: External stakeholder access via portal

**Features**:

- Portal user authentication
- Limited read-only access
- Flight information display
- Security group separation
- Custom portal templates

### 7. Flight UOM

**Purpose**: Aviation-specific units of measurement

**Features**:

- Aviation units (nautical miles, feet, knots)
- Weight units (pounds, kilograms)
- Volume units (gallons, liters)
- Conversion factors
- Integration with Odoo's UOM system

### 8. Website Flight Fleet

**Purpose**: Public website features for fleet display

**Key Models**:

- `flight.aircraft.image` - Aircraft images
- `flight.aircraft.image.category` - Image categories
- `website.snippet.filter` - Dynamic content filters

**Features**:

- Public fleet listing page
- Aircraft detail pages
- Image galleries
- Dynamic snippets for website builder
- Search and filtering
- Responsive design

## Data Models

### Core Entity Relationships

```sql
-- Simplified ERD
flight.flight
    ├── aircraft_id → flight.aircraft
    ├── departure_id → flight.aerodrome
    ├── arrival_id → flight.aerodrome
    └── crew_ids → flight.crew[]

flight.aircraft
    ├── model_id → flight.aircraft.model
    ├── operator_id → res.partner
    └── spec_ids → flight.aircraft.spec[]

flight.aerodrome
    ├── country_id → res.country
    └── state_id → res.country.state

flight.crew
    ├── flight_id → flight.flight
    ├── partner_id → res.partner
    └── role_id → flight.crew.role
```

### Key Model Fields

#### flight.flight

- `date` (Date): Scheduled flight date
- `aircraft_id` (Many2one): Aircraft reference
- `departure_id` (Many2one): Departure aerodrome
- `arrival_id` (Many2one): Arrival aerodrome
- `crew_ids` (One2many): Assigned crew members
- `locked` (Boolean): Record lock status

#### flight.aircraft

- `registration` (Char): Aircraft registration number
- `model_id` (Many2one): Aircraft model
- `operator_id` (Many2one): Operating company
- `sn` (Char): Serial number
- `dom` (Date): Date of manufacture
- `equipment_type` (Selection): Equipment classification
- `mtow` (Float): Maximum takeoff weight

#### flight.aerodrome

- `icao` (Char): ICAO code
- `iata` (Char): IATA code
- `name` (Char): Airport name
- `city` (Char): City location
- `country_id` (Many2one): Country
- `latitude` (Float): GPS latitude
- `longitude` (Float): GPS longitude
- `elevation` (Integer): Elevation in feet

## Security Model

### Access Groups Hierarchy

```
Flight Management
├── User (Read-only access)
├── Crew (Update flight information)
├── Dispatcher (Manage flights and data)
└── Manager (Full access and configuration)
```

### Group Permissions

| Group      | Read | Write | Create | Delete | Configure |
| ---------- | ---- | ----- | ------ | ------ | --------- |
| User       | ✓    | -     | -      | -      | -         |
| Crew       | ✓    | ✓     | -      | -      | -         |
| Dispatcher | ✓    | ✓     | ✓      | -      | -         |
| Manager    | ✓    | ✓     | ✓      | ✓      | ✓         |

### Portal Access

- Limited to read-only operations
- Restricted to published records
- Separate security group: `flight.group_portal_user`

## API Reference

### Model Methods

#### flight.flight

```python
def name_get(self):
    """Generate display name for flight record
    Returns: [(id, "date / registration: DEP - ARR")]
    """

def toggle_locked(self):
    """Toggle flight lock status
    Prevents modifications when locked
    """

@api.onchange('aircraft_id')
def _onchange_aircraft_id(self):
    """Auto-populate departure from last arrival
    Sets departure to aircraft's last known location
    """
```

#### flight.aircraft

```python
@api.constrains('registration')
def _check_registration_unique(self):
    """Ensure aircraft registration is unique
    Raises: ValidationError if duplicate found
    """
```

#### flight.event.time

```python
def _create_phase_durations(self, new_events):
    """Automatically create phase duration records
    Links start and end events for phase tracking
    """

def action_view_time_changes(self):
    """Open history of time changes
    Returns: Action dictionary for history window
    """
```

### Controller Endpoints

#### Website Flight Fleet

```python
@http.route(['/fleet', '/fleet/page/<int:page>'],
            type='http', auth='public', website=True)
def fleet(self, page=1, model=None, search=None):
    """Public fleet listing page

    Args:
        page: Page number for pagination
        model: Filter by aircraft model
        search: Search term for filtering

    Returns: Rendered fleet page template
    """

@http.route(['/aircraft/<model("flight.aircraft"):aircraft>'],
            type='http', auth='public', website=True)
def aircraft_detail(self, aircraft):
    """Aircraft detail page

    Args:
        aircraft: Aircraft record

    Returns: Rendered detail page template
    """

@http.route(['/flight/aircraft/images'],
            type='json', auth='public')
def get_aircraft_images(self, category_id=None, aircraft_id=None):
    """AJAX endpoint for aircraft images

    Args:
        category_id: Filter by image category
        aircraft_id: Filter by specific aircraft

    Returns: JSON with image data
    """
```

## Frontend Components

### OWL Components (JavaScript)

#### Flight Event Time Matrix

**Location**: `flight_event/static/src/components/`

**Components**:

- `FlightEventTimeMatrixField` - Main field widget
- `FlightEventTimeMatrixRenderer` - Matrix renderer
- `FlightEventTimeMatrixCell` - Individual matrix cell component

**Usage**:

```javascript
/** @odoo-module **/
import { Component } from "@odoo/owl";

export class FlightEventTimeMatrixField extends Component {
  static template = "flight_event.TimeMatrixField";

  setup() {
    // Component initialization
  }
}
```

### Website Snippets

**Dynamic Aircraft Images Snippet**:

- Displays aircraft images dynamically
- Filterable by category and aircraft
- AJAX-powered content loading

**Multiple Carousel Snippet**:

- Responsive image carousel
- Touch-enabled navigation
- Auto-play functionality

## Installation & Deployment

### Prerequisites

```bash
# System Requirements
- Odoo 18.0 CE
- Python 3.11+
- PostgreSQL 13+
- Node.js 16+ (for frontend assets)

# Python Dependencies
pip install -r requirements.txt
```

### Installation Steps

1. **Clone Repository**

```bash
git clone https://github.com/smartops-aero/smartops-odoo-flight.git
cd smartops-odoo-flight
git checkout 18.0
```

2. **Configure Odoo**

```bash
# Add to odoo.conf
[options]
addons_path = /path/to/smartops-odoo-flight,/path/to/odoo/addons
```

3. **Install Modules**

```bash
# Install base module and dependencies
odoo -c odoo.conf -i flight_uom,flight

# Install additional modules as needed
odoo -c odoo.conf -i flight_event,flight_aircraft_spec,website_flight_fleet
```

4. **Load Aerodrome Data**

```bash
# Download large dataset
wget https://raw.githubusercontent.com/smartops-aero/smartops-odoo-flight/18.0/flight/data/flight.aerodrome.csv

# Import via UI: Flights -> Configuration -> Aerodromes -> Import
```

### Development Mode

```bash
# Run with auto-reload for development
odoo -c odoo.conf --dev=reload

# Run with specific log level
odoo -c odoo.conf --log-level=debug
```

### Testing

```bash
# Run all tests
odoo -c odoo.conf --test-enable --stop-after-init -i flight

# Run specific test module
odoo -c odoo.conf --test-enable --stop-after-init -i flight_event

# Generate coverage report
coverage run odoo -c odoo.conf --test-enable --stop-after-init -i flight
coverage report
coverage html
```

## Development Guidelines

### Code Style

**Python**:

- Use Ruff for linting and formatting
- Target Python 3.11+ features
- Follow Odoo coding conventions

```bash
# Format code
ruff format .

# Check and fix issues
ruff check . --fix
```

**JavaScript**:

- ES6+ modules with `/** @odoo-module **/`
- OWL Framework 2.0 patterns
- ESLint with Odoo config

```bash
# Lint JavaScript
npx eslint . --fix
```

**XML/HTML**:

- Prettier for formatting
- Proper indentation (4 spaces)
- Semantic HTML5

```bash
# Format templates
npx prettier --write "**/*.{xml,html,css}"
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Git Workflow

**Branch Strategy**:

- Main branch: `18.0` (current version)
- Feature branches: `18.0-feature-name`
- Hotfix branches: `18.0-hotfix-description`

**Commit Messages**:

```
[MODULE] Brief description

Detailed explanation of changes
- Bullet point 1
- Bullet point 2

Fixes #issue_number
```

### Migration Guidelines

**Version Migrations**:

- Place scripts in `migrations/{version}/`
- Use `pre-migrate.py` for schema changes
- Use `post-migrate.py` for data migration

**Example Migration**:

```python
# migrations/18.0.1.0.0/post-migrate.py
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Migration logic here
```

### Security Best Practices

1. **Access Control**:

   - Define explicit access rights in CSV
   - Use record rules for row-level security
   - Test with different user roles

2. **Data Validation**:

   - Use constraints for data integrity
   - Validate user inputs
   - Sanitize external data

3. **Portal Access**:
   - Limit fields exposed to portal
   - Use separate views for portal
   - Check website_published flag

### Performance Optimization

1. **Database**:

   - Add indexes for frequently queried fields
   - Use SQL constraints where possible
   - Optimize domain filters

2. **Python**:

   - Use `@api.depends_context` for context-dependent computes
   - Batch operations with `create()` and `write()`
   - Avoid N+1 queries with prefetch

3. **Frontend**:
   - Lazy load components
   - Minimize DOM manipulations
   - Use pagination for large datasets

## Troubleshooting

### Common Issues

**Module Not Found**:

```bash
# Check addons path
odoo shell -c odoo.conf
>>> from odoo import modules
>>> modules.get_modules()
```

**Access Rights Error**:

```bash
# Regenerate access rights
odoo -c odoo.conf -u flight --stop-after-init
```

**JavaScript Errors**:

```bash
# Clear assets
odoo -c odoo.conf --dev=xml,reload,qweb
```

**Migration Failures**:

```bash
# Check migration scripts
ls migrations/*/
# Verify version in __manifest__.py
```

## Support & Resources

### Documentation

- [Odoo 18.0 Documentation](https://www.odoo.com/documentation/18.0/)
- [OWL Framework Guide](https://github.com/odoo/owl)
- [Project Repository](https://github.com/smartops-aero/smartops-odoo-flight)

### Community

- GitHub Issues: Report bugs and request features
- Discussions: Technical questions and best practices
- Wiki: Additional guides and tutorials

### License

- **Code**: LGPL-3.0
- **Documentation**: CC BY-SA 4.0
- **Assets**: See individual licenses

---

_Last updated: 2025-08-13_
_Version: 18.0.1.0.0_
