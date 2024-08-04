# -*- coding: utf-8 -*-
{
    'name': "Flight Number",

    'summary': """
        Adds a flight number and flight prefix fields to Flight module.""",

    'description': """
            Adds a flight number and flight prefix fields to Flight module.""",

    'author': "Apexive Solutions LLC",
    'website': "https://apexive.com",
    'license': "Other OSI approved licence",
    'category': 'Industries',
    'version': '16.0.0.3',

    'depends': [
        'base',
        'flight',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/flight_views.xml',
        'views/flight_number_views.xml',
        'views/flight_prefix_views.xml',
        'views/menu.xml',
    ],
}
