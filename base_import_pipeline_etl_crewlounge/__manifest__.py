{
    'name': 'Base Import Pipeline ETL - CrewLounge',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Import CrewLounge CSV data into flight models',
    'description': """
        This module provides a specialized ETL pipeline for importing 
        CrewLounge CSV data into flight models.
    """,
    'depends': [
        'base_import_pipeline_etl',
        'flight',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/import_pipeline_data.xml',
        'wizards/crewlounge_import_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
