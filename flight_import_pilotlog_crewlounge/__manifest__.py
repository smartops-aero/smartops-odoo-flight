# Copyright 2024 Apexive <https://apexive.com/>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    'name': 'Flight Import - Pilot Log (CrewLounge)',
    'version': '1.0',
    'category': 'Flight',
    'summary': 'Import flight data from CrewLounge CSV format',
    'author': 'Apexive',
    'website': 'https://apexive.com',
    'license': 'LGPL-3',
    'depends': ['flight', 'flight_pilotlog'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/crewlounge_import_wizard_views.xml',
        'views/menus.xml',
    ],
    'external_dependencies': {
        'python': ['petl'],
    },
    'installable': True,
    'application': False,
}
