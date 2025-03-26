# -*- coding: utf-8 -*-
{
    'name': 'Flight Import PilotLog',
    'version': '1.0',
    'category': 'Flight',
    'summary': 'Base module for importing pilot log data',
    'description': """
Flight Import PilotLog
======================
Base module for importing pilot log data with flexible transformers.
    """,
    'depends': ['base_import', 'flight'],
    'data': [
        'security/ir.model.access.csv',
        'views/flight_import_pilotlog_transformer_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'flight_import_pilotlog/static/src/js/import.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
