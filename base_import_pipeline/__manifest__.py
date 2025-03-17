{
    "name": "Base Import Pipeline",
    "summary": """
        Base framework for creating import pipelines""",
    "description": """
        This module provides a base framework for creating flexible import pipelines
        using a dispatch pattern for implementing different import strategies.
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "license": "LGPL-3",
    "category": "Technical",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/base_import_pipeline_views.xml",
        "views/menu.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
