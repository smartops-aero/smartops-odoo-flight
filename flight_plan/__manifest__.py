{
    "name": "Flight Plan",
    "summary": "Models for storing flight plan routes and waypoints",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/flight",
    "depends": ["flight", "flight_event", "flight_json_widget"],
    "data": [
        "security/ir.model.access.csv",
        "views/flight_plan_views.xml",
        "views/flight_plan_route_views.xml",
        "views/flight_route_waypoint_views.xml",
        "views/flight_plan_aerodrome_views.xml",
        "views/menu.xml",
    ],
    "images": [
        "static/description/banner.jpeg",
    ],
}
