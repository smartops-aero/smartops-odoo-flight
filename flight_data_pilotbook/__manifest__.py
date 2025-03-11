{
    'name': 'Flight Data - Pilot Book',
    'version': '16.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Import pilots from CSV and add them as partners',
    'description': """
        This module provides a flexible import wizard for pilots from CSV files into Odoo contacts.
        Features include:
        - CSV upload with field mapping
        - Data preview before import
        - Conflict detection and resolution
        - Validation of imported data
    """,
    'author': 'Apexive Solutions LLC',
    'website': 'https://www.apexive.com',
    'depends': [
        'base',
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/pilot_import_template.xml',
        'wizards/pilot_import_views.xml',
        'views/menu_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
