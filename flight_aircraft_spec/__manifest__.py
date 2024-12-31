{
    "name": "Flight Aircraft Specifications",
    "version": "16.0.1.0.1",
    "category": "Flight",
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "summary": "Comprehensive aircraft specifications management system",
    "description": """
        Provides a robust and flexible system for managing aircraft specifications and amenities:

        Key Features:
        - Categorize aircraft specifications with custom categories
        - Define specification codes with different value types (Boolean, Text, Float)
        - Associate specifications with individual aircraft
        - Support for translatable names and descriptions
        - Automatic unit of measure handling
        - Seat map image storage
        - Tracking of specification changes

        This module replaces and consolidates the previous flight_aircraft_specifications
        and flight_aircraft_amenities modules, offering a more comprehensive and
        extensible approach to aircraft specification management.
    """,
    "depends": [
        "base",
        "flight",
        "uom",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/flight_aircraft_views.xml",
        "views/flight_aircraft_spec_views.xml",
        "views/menus.xml",
        "data/flight_aircraft_spec_data.xml",
    ],
    "images": [
        "static/description/banner.png",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
