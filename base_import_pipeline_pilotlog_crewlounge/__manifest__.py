{
    "name": "CrewLounge Pilot Log Import",
    "summary": """
        Import CrewLounge pilot log data into flight records""",
    "description": """
        This module extends the base import pipeline ETL module to provide
        specific functionality for importing CrewLounge pilot log data into
        flight records.
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "license": "LGPL-3",
    "category": "Industries",
    "version": "16.0.1.0.0",
    "depends": [
        "base_import_pipeline_etl",
        "flight",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/crewlounge_pilot_log_import_views.xml",
        "data/crewlounge_pilot_log_import_data.xml",
        "views/menu.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
