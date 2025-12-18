{
    "name": "Flight Events",
    "summary": """
        A technical module for tracking flight events and phases.""",
    "description": """
        This module extends the base Flight module to provide tracking of flight events and phases, e.g. takeoff, landing, etc times
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/smartops-odoo-flight",
    "license": "LGPL-3",
    "category": "Industries",
    "version": "18.0.1.2.0",
    "depends": [
        "base",
        "flight",
        "web",
    ],
    "assets": {
        "web.assets_backend": [
            # Shared hooks
            "flight_event/static/src/hooks/*.js",
            # Shared time input cell (used by both matrix and summary widgets)
            "flight_event/static/src/components/flight_time_input_cell/flight_time_input_cell.scss",
            "flight_event/static/src/components/flight_time_input_cell/flight_time_input_cell.js",
            "flight_event/static/src/components/flight_time_input_cell/flight_time_input_cell.xml",
            # Matrix widget
            "flight_event/static/src/scss/flight_event_time_matrix.scss",
            "flight_event/static/src/components/flight_event_time_matrix_cell/flight_event_time_matrix_cell.js",
            "flight_event/static/src/components/flight_event_time_matrix_field/flight_event_time_matrix_field.js",
            "flight_event/static/src/components/flight_event_time_matrix_renderer/flight_event_time_matrix_renderer.js",
            "flight_event/static/src/components/flight_event_time_matrix_cell/flight_event_time_matrix_cell.xml",
            "flight_event/static/src/components/flight_event_time_matrix_field/flight_event_time_matrix_field.xml",
            "flight_event/static/src/components/flight_event_time_matrix_renderer/flight_event_time_matrix_renderer.xml",
            # Summary widget
            "flight_event/static/src/components/flight_time_summary/flight_time_summary.scss",
            "flight_event/static/src/components/flight_time_summary/flight_time_summary.js",
            "flight_event/static/src/components/flight_time_summary/flight_time_summary.xml",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/flight_event_code_views.xml",
        "views/flight_event_time_views.xml",
        "views/flight_phase_views.xml",
        "views/flight_views.xml",
        "views/flight_phase_duration_views.xml",
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
