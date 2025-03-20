{
    "name": "Base Import Pipeline ETL",
    "summary": """
        ETL implementation for base import pipeline""",
    "description": """
        This module adds ETL (Extract, Transform, Load) capabilities to the
        base import pipeline framework. It provides CSV file handling,
        field mapping, and transformation functionality.
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "license": "LGPL-3",
    "category": "Technical",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
        "base_import_pipeline",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/base_import_pipeline_etl_views.xml",
        "views/base_import_pipeline_mapping_views.xml",
        "views/menu.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
