{
    "name": "Aircraft Fleet Website",
    "category": "Website/Website",
    "sequence": 200,
    "website": "https://github.com/smartops-aero/flight",
    "summary": "Publish aircraft details and fleet information online",
    "version": "16.0.1.0.0",
    "depends": ["website", "flight"],
    "data": [
        "security/ir.model.access.csv",
        "security/website_flight_fleet_security.xml",
        "data/website_flight_fleet_data.xml",
        # Snippets
        "views/snippets/s_website_flight_fleet_accordion.xml",
        "views/snippets/s_website_flight_fleet_carousel.xml",
        "views/snippets/s_website_flight_fleet_multiple_carousel.xml",
        # Snippets Registration and options
        "views/snippets/options.xml",
        "views/snippets/snippets.xml",
        "views/pages/page_fleet.xml",
        "views/pages/page_aircraft_detail.xml",
        "views/flight_aircraft_views.xml",
        "views/menu.xml",
        "views/website_flight_fleet_views.xml",
    ],
    "assets": {
        "website.assets_wysiwyg": [
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_multiple_carousel/options.js",
        ],
        "web.assets_frontend": [
            "website_flight_fleet/static/src/scss/website_flight_fleet.scss",
            "website_flight_fleet/static/src/js/website_flight_fleet.js",
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_carousel/000.scss",
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_multiple_carousel/000.scss",
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_multiple_carousel/000.js",
            "website_flight_fleet/static/src/snippets/s_website_flight_fleet_accordion/000.scss",
        ],
        "website.assets_editor": [
            "website_flight_fleet/static/src/js/systray_items/new_content.js",
        ],
    },
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
