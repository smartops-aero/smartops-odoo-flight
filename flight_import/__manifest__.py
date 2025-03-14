# -*- coding: utf-8 -*-
{
    'name': 'Flight Import',
    'version': '16.0.1.0.0',
    'category': 'Flight',
    'summary': 'Import flight data from various sources',
    'description': """
Flight Import
=================
This module provides a framework for importing flight data from various sources.
It extends the base_import module with specialized functionality for flight data.
    """,
    'author': 'Apexive',
    'website': 'https://apexive.com',
    'depends': [
        'base_import',
        'flight',
        'flight_pilotlog',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/flight_data_importer_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
