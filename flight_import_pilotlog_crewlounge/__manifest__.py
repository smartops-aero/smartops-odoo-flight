# -*- coding: utf-8 -*-
{
    'name': 'Flight Import PilotLog CrewLounge',
    'version': '1.0',
    'category': 'Flight',
    'summary': 'CrewLounge format importer for pilot logs',
    'description': """
Flight Import PilotLog CrewLounge
=================================
Adds support for importing pilot log data from CrewLounge format.
    """,
    'depends': ['flight_import_pilotlog'],
    'data': [
        'data/flight_import_transformer_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
