{
    "name": "Flight Widget - Map View",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "summary": "Interactive map widget for Odoo with route visualization and animation",
    "description": """
Flight Map View Widget
======================

Interactive map widget for Odoo 18.0 with advanced route visualization, path animation, and geographic data display capabilities.

Key Features
------------
* **Interactive Maps**: Leaflet-based map widget with OpenStreetMap integration
* **Route Visualization**: Display flight paths between departure and arrival points
* **Path Animation**: GSAP-powered smooth animations for route display
* **Coordinate Support**: Handle various coordinate formats (decimal, DMS, arcseconds)
* **Customizable Markers**: Support for custom icons and marker styles
* **Responsive Design**: Adapts to different screen sizes and form layouts
* **Real-time Updates**: Dynamic map updates based on field changes

Technical Features
------------------
* Built on Leaflet.js for robust mapping
* GSAP animation library for smooth transitions
* Support for multiple coordinate systems
* Automatic bounds fitting
* Zoom controls and pan functionality
* Mobile-friendly touch gestures

Use Cases
---------
* Aviation route display
* Logistics tracking
* Geographic data visualization
* Location-based planning
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/smartops-odoo-flight",
    "depends": ["base", "web"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "flight_widget_map_view/static/lib/leaflet/leaflet.css",
            "flight_widget_map_view/static/lib/leaflet/leaflet.js",
            "flight_widget_map_view/static/lib/gsap/gsap.min.js",
            "flight_widget_map_view/static/src/js/flight_map_view_field.js",
            "flight_widget_map_view/static/src/scss/flight_map_view_field.scss",
            "flight_widget_map_view/static/src/xml/flight_map_view_field.xml",
        ],
    },
    "images": [
        "static/description/banner.jpeg",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
