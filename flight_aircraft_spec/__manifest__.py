{
    "name": "Flight Aircraft Specifications",
    "version": "16.0.1.0.0",
    "category": "Flight",
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "summary": "Manage aircraft specifications and amenities",
    "description": """
        This module provides a unified way to manage aircraft specifications and amenities.
        It replaces the existing flight_aircraft_specifications and flight_aircraft_amenities modules.
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
