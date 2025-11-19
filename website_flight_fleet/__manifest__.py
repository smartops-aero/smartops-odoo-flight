{
    "name": "Aircraft Fleet Website",
    "category": "Industries",
    "sequence": 200,
    "summary": """Publish aircraft details and fleet information online""",
    "description": """
        This module provides website integration for displaying aircraft fleet information.
        It allows you to showcase your aircraft fleet online with detailed specifications
        and amenities information using beautiful and responsive website snippets.

        Features:
        - Beautiful website snippets for fleet display
        - Accordion and carousel display options
        - Integration with specifications and amenities modules
        - Responsive design for all devices
        - Customizable display options
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/smartops-odoo-flight",
    "version": "18.0.1.0.0",
    "depends": [
        "website",
        "flight",
        "flight_aircraft_spec",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/website_flight_fleet_security.xml",
        "data/website_flight_fleet_data.xml",
        # Snippets
        "views/snippets/s_website_flight_fleet_accordion.xml",
        "views/snippets/s_website_flight_fleet_carousel.xml",
        "views/snippets/s_website_flight_fleet_multiple_carousel.xml",
        "views/snippets/s_website_flight_fleet_dynamic_aircraft_images.xml",
        # Snippets Registration and options
        "views/snippets/options.xml",
        "views/snippets/snippets.xml",
        "views/pages/page_fleet.xml",
        "views/pages/page_aircraft_detail.xml",
        "views/flight_aircraft_views.xml",
        "views/website_flight_fleet_views.xml",
        "views/website_flight_fleet_templates.xml",
    ],
    "assets": {
        "website.assets_wysiwyg": [
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_multiple_carousel/options.js",
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_dynamic_aircraft_images/options.js",
        ],
        "web.assets_frontend": [
            "website_flight_fleet/static/src/scss/website_flight_fleet.scss",
            "website_flight_fleet/static/src/js/website_flight.js",
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_carousel/000.scss",
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_multiple_carousel/000.scss",
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_multiple_carousel/000.js",
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_accordion/000.scss",
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_dynamic_aircraft_images/000.js",
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_dynamic_aircraft_images/000.scss",
        ],
        "website.assets_editor": [
            "website_flight_fleet/static/src/js/systray_items/new_content.js",
        ],
    },
    "images": [
        "static/description/banner.jpeg",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
