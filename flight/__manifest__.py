# -*- coding: utf-8 -*-
{
    'name': "Flight",

    'summary': """
        Base module for managing flights, aircraft, and aerodromes.""",

    'description': """
        This module provides basic models and views for the management of flights, aircraft, and aerodromes and
        is used by other modules to provide more advanced functionality.
        
        See Flight Operations Management (flight_ops) module for user interface and business logic.
        
        === Aerodrome Data ===
            Because of the large size of the aerodrome data, it is not loaded by default. To load the data, download the CSV
            file from https://raw.githubusercontent.com/smartops-aero/smartops-odoo-flight/16.0/flight/data/flight.aerodrome.csv
            and import it using the Flights -> Configuration -> Aerodromes -> Favorites -> Import records function.
    """,
    'author': "Apexive Solutions LLC",
    'website': "https://github.com/smartops-aero/smartops-odoo-flight",
    'license': "LGPLv3",
    'category': 'Industries',
    'version': '16.0.0.3',

    'depends': [
        'base',
        'mail',
    ],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/flight_views.xml',
        'views/aircraft_views.xml',
        'views/aerodrome_views.xml',
        'views/menu.xml',
        'data/flight.aircraft.class.csv',
        'data/flight.aircraft.model.tag.csv',
        # 'data/flight.aerodrome.csv',
    ],
}
