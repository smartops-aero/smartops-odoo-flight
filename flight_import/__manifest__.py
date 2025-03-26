{
    'name': 'Flight Import',
    'version': '16.0.0.1.0',
    'category': 'Customizations',
    'summary': 'Enhanced import for flight logs',
    'description': """
        Import flight logs from various formats including CrewLounge.
        Provides specialized import UX for the flight.flight model.
    """,
    'depends': ['base_import', 'flight_pilotlog'],
    'assets': {
        'web.assets_backend': [
            'flight_import/static/src/js/base_import.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}