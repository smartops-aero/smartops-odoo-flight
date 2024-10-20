{
    "name": "Flight Events",
    "summary": """
        A technical module for tracking flight events and phases.""",
    "description": """
        This module extends the base Flight module to provide tracking of flight events and phases, e.g. takeoff, landing, etc times
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/OCA/server-env",
    "license": "LGPL-3",
    "category": "Industries",
    "version": "16.0.0.5",
    "depends": [
        "base",
        "flight",
    ],
    "assets": {
        "web.assets_backend": [
            "flight_event/static/src/components/relative_datetimepicker/relative_datetimepicker.esm.js",
            "flight_event/static/src/scss/flight_event_time_matrix.scss",
            "flight_event/static/src/components/flight_event_time_matrix_field/flight_event_time_matrix_field.esm.js",
            "flight_event/static/src/components/flight_event_time_matrix_renderer/flight_event_time_matrix_renderer.esm.js",
            "flight_event/static/src/components/flight_event_time_matrix_field/flight_event_time_matrix_field.xml",
            "flight_event/static/src/components/flight_event_time_matrix_renderer/flight_event_time_matrix_renderer.xml",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/flight_event_code_views.xml",
        "views/flight_event_time_views.xml",
        "views/flight_phase_views.xml",
        "views/flight_views.xml",
        "data/flight.event.code.csv",
        "data/flight.phase.csv",
        "views/menu.xml",
    ],
    "images": [
        "static/description/banner.jpeg",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
