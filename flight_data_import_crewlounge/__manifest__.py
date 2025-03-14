# -*- coding: utf-8 -*-
{
    'name': 'Flight Data Import - CrewLounge PILOTLOG',
    'version': '1.0',
    'category': 'Flight',
    'summary': 'Import flight data from CrewLounge PILOTLOG format',
    'description': """
        This module provides support for importing flight data from CrewLounge PILOTLOG CSV format.
        It extends the flight_data_import module with specific mappings and parsing logic for CrewLounge data.
    """,
    'author': 'Apexive',
    'website': 'https://www.apexive.com',
    'depends': [
        'flight_data_import',
        'flight',
        'flight_pilotlog',
    ],
    'data': [
        'data/flight_import_template_data.xml',
        'data/flight_import_mapping_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
