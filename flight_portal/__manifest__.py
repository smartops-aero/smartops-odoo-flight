{
    "name": "Flight Portal",
    "summary": """
        Portal access for flight information""",
    "description": """
        This module adds portal functionality to the Flight module,
        allowing sharing of flight information via secure access tokens.
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "license": "LGPL-3",
    "category": "Industries",
    "version": "18.0.1.0.0",
    "depends": [
        "flight",
        "portal",
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/flight_portal_security.xml",
        "views/flight_views.xml",
        "views/flight_portal_templates.xml",
    ],
    "images": [
        "static/description/banner.jpeg",
    ],
    "installable": True,
    "auto_install": False,
}
