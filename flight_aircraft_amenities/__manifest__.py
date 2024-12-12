{
    "name": "Aircraft Amenities",
    "category": "Industries",
    "sequence": 196,
    "summary": """Manage aircraft amenities and comfort features""",
    "description": """
        This module extends the flight module to manage aircraft amenities and comfort features.
        It allows you to define and track various amenities available in different aircraft,
        helping to maintain a detailed inventory of comfort features.
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "version": "16.0.1.0.0",
    "depends": ["flight"],
    "data": [
        "security/ir.model.access.csv",
        "views/flight_aircraft_views.xml",
        "views/amenities_menus.xml",
        "data/flight_aircraft_amenity_data.xml",
    ],
    "images": [
        "static/description/banner.png",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}