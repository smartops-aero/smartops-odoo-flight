{
    "name": "Flight Import",
    "summary": """
        Import flight data from various formats (CrewLounge, LogTen Pro, etc.)
    """,
    "description": """
        This module provides a flexible, configurable system for importing flight data 
        from various logbook applications and formats into the Flight Management system.
        
        Features:
        - Configurable import mappings through a user-friendly interface
        - Support for different file formats through custom configurations
        - Pre-configured mapping for CrewLounge PilotLog
        - Import of flight data, aircraft information, pilot times, and events
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "license": "LGPL-3",
    "category": "Industries",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
        "flight",
        "flight_pilotlog",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/import_wizard_views.xml",
        "views/import_config_views.xml",
        "data/default_import_config.xml",
    ],
    "demo": [],
    "application": False,
    "installable": True,
    "auto_install": False,
}