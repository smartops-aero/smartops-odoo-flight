{
    "name": "Flight Pilot Log",
    "summary": """
        Pilot logbook for tracking and managing pilot flight times.""",
    "description": """
        A comprehensive module for managing pilot logbooks, including:
        - Tracking different types of pilot time (PIC, SIC, etc.)
        - Recording flight events and responsibilities
        - Integrating with flight management
        - Generating pilot reports and statistics
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "license": "LGPL-3",
    "category": "Industries",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
        "flight",
        "flight_event",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/flight_pilot_time_code_data.xml",
        "views/flight_pilot_time_views.xml",
        "views/flight_pilot_event_views.xml",
        "views/flight_pilot_time_code_views.xml",
        "views/menu.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}