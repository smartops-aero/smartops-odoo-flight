{
    "name": "Flight Data Sync - OpenSky Network",
    "version": "18.0.1.0.0",
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/smartops-odoo-flight",
    "license": "LGPL-3",
    "category": "Industries",
    "summary": "Synchronize flight data with OpenSky Network API",
    "description": """
Flight Data Sync - OpenSky Network
===================================

Integrates with the OpenSky Network API to synchronize flight data.

Features:
---------
* Fetch flights by aircraft and date range
* Compare OpenSky data with existing flights
* Create, update or skip flights based on user selection
* Interactive wizard for flight synchronization
* Automatic aircraft registration matching

The OpenSky Network is a non-profit association that provides free access
to real-time and historical ADS-B flight data for research and non-commercial use.

For more information, visit: https://opensky-network.org/
    """,
    "depends": [
        "flight",
        "flight_data_sync",
    ],
    "external_dependencies": {
        "python": ["requests"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/flight_data_provider_views.xml",
        "wizard/opensky_sync_wizard_views.xml",
    ],
    "demo": [],
    "images": [
        "static/description/banner.png",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
