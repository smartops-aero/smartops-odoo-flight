# pre-migration.py
from odoo.upgrade import util
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    if not version:
        return

    _logger.info("Starting website_flight_fleet pre-migration")

    # 1. Store all current values before removing structures
    # Store amenity data before dropping model
    if util.table_exists(cr, 'flight_aircraft_amenity'):
        _logger.info("Storing amenity data for migration")
        util.logged_query(
            cr, """
            INSERT INTO ir_property (name, value_text, type, fields_id, res_id)
            SELECT 
                'temp_amenity_' || rel.aircraft_id || '_' || a.id,
                a.name,
                'text',
                (SELECT id FROM ir_model_fields WHERE model='flight.aircraft' AND name='website_description'),
                'flight.aircraft,' || rel.aircraft_id::text
            FROM flight_aircraft_amenity_rel rel
            JOIN flight_aircraft_amenity a ON rel.amenity_id = a.id
            """
        )

    # Store specifications before removing their columns
    specs_to_store = {
        'passenger_capacity': 'load.passengers',
        'range_nm': 'performance.range',
        'cruise_speed': 'performance.cruise_speed',
        'cabin_length': 'cabin.length',
        'cabin_width': 'cabin.width',
        'cabin_height': 'cabin.height',
        'luggage_capacity': 'load.luggage',
        'useful_load': 'load.useful_load',
    }

    for old_field, spec_code in specs_to_store.items():
        if util.column_exists(cr, 'flight_aircraft', old_field):
            _logger.info(f"Storing {old_field} data for migration to {spec_code}")
            util.logged_query(
                cr, f"""
                INSERT INTO ir_property (name, value_float, type, fields_id, res_id)
                SELECT 
                    'temp_spec_{spec_code}_' || id,
                    {old_field},
                    'float',
                    (SELECT id FROM ir_model_fields WHERE model='flight.aircraft' AND name='website_description'),
                    'flight.aircraft,' || id::text
                FROM flight_aircraft 
                WHERE {old_field} IS NOT NULL
                """
            )

    # Store HTML content before removing fields
    html_fields = [
        'hero_content', 'spec_header_content', 'interior_gallery_header_content',
        'benefits_content', 'faq_header_content', 'faq_content',
        'main_carousel_content', 'interior_gallery_carousel_content', 'cta_content'
    ]
    
    existing_html_fields = [f for f in html_fields if util.column_exists(cr, 'flight_aircraft', f)]
    if existing_html_fields:
        _logger.info("Storing HTML content for migration")
        concat_fields = ' || '.join(f"COALESCE({field}, '')" for field in existing_html_fields)
        util.logged_query(
            cr, f"""
            INSERT INTO ir_property (name, value_text, type, fields_id, res_id)
            SELECT 
                'temp_html_content_' || id,
                {concat_fields},
                'text',
                (SELECT id FROM ir_model_fields WHERE model='flight.aircraft' AND name='website_description'),
                'flight.aircraft,' || id::text
            FROM flight_aircraft
            WHERE {' OR '.join(f"{field} IS NOT NULL" for field in existing_html_fields)}
            """
        )

    # 2. Remove old structures
    # Remove old HTML fields
    for field in html_fields:
        if util.column_exists(cr, 'flight_aircraft', field):
            _logger.info(f"Removing field {field}")
            util.remove_field(cr, 'flight.aircraft', field, cascade=True)

    # Remove old specification fields
    for field in specs_to_store:
        if util.column_exists(cr, 'flight_aircraft', field):
            _logger.info(f"Removing field {field}")
            util.remove_field(cr, 'flight.aircraft', field, cascade=True)

    # Remove amenity model and its relations
    if util.table_exists(cr, 'flight_aircraft_amenity'):
        _logger.info("Removing amenity model")
        util.remove_model(cr, 'flight.aircraft.amenity', cascade=True)