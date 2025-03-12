# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

{
    "name": "Flight Data Import Base",
    "summary": "Base module for importing flight data",
    "version": "16.0.1.0.0",
    "category": "Flight Management",
    "license": "LGPL-3",
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "depends": ["base", "flight"],
    "data": [
        "views/flight_flight_views.xml",
        "views/menu_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
