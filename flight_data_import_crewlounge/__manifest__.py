# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

{
    "name": "Flight Data Import - CrewLounge",
    "summary": "Import pilots and aircraft from CrewLounge CSV exports",
    "version": "16.0.1.0.0",
    "category": "Flight Management",
    "license": "LGPL-3",
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "depends": ["base", "flight", "flight_data_import"],
    "data": [
        "security/ir.model.access.csv",
        "views/menu_views.xml",
        "wizards/pilot_import_views.xml",
        "wizards/aircraft_import_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
