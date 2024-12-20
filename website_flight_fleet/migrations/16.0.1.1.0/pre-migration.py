# pre-migration.py
import logging

_logger = logging.getLogger(__name__)

def table_exists(cr, table):
    """Check if table exists in database"""
    try:
        cr.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table,))
        return cr.fetchone()[0]
    except Exception as e:
        _logger.error(f"Error checking table existence for {table}: {str(e)}")
        return False

def get_table_columns(cr, table):
    """Get column names for a table"""
    try:
        cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s
        """, (table,))
        return [row[0] for row in cr.fetchall()]
    except Exception as e:
        _logger.error(f"Error getting columns for table {table}: {str(e)}")
        return []

def column_exists(cr, table, column):
    """Check if column exists in table"""
    try:
        cr.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            )
        """, (table, column))
        return cr.fetchone()[0]
    except Exception as e:
        _logger.error(f"Error checking column existence for {table}.{column}: {str(e)}")
        return False

def migrate(cr, version):
    if not version:
        return

    _logger.info("Starting website_flight_fleet pre-migration")

    # Create temporary migration table
    try:
        cr.execute("""
            CREATE TABLE IF NOT EXISTS website_fleet_migration (
                id serial PRIMARY KEY,
                aircraft_id integer,
                data_type varchar,  -- 'spec' or 'amenity'
                name varchar,       -- spec code or amenity name
                float_value float,  -- for numeric specs
                bool_value boolean, -- for boolean specs
                category_name varchar, -- for grouping
                sequence integer    -- for ordering
            )
        """)
    except Exception as e:
        _logger.error(f"Failed to create migration table: {str(e)}")
        return

    # Store amenity data if tables exist
    rel_table = 'flight_aircraft_amenity_rel'
    amenity_table = 'flight_aircraft_amenity'

    if table_exists(cr, rel_table) and table_exists(cr, amenity_table):
        _logger.info("Found amenity tables, checking columns")
        
        try:
            # Extract and store amenity relationships
            _logger.info("Storing amenity data for migration")
            cr.execute(f"""
                INSERT INTO website_fleet_migration (
                    aircraft_id, 
                    data_type, 
                    name, 
                    bool_value,
                    sequence
                )
                SELECT 
                    rel.aircraft_id, 
                    'amenity', 
                    a.name, 
                    true,
                    a.sequence
                FROM {rel_table} rel
                JOIN {amenity_table} a ON rel.amenity_id = a.id
            """)
            _logger.info("Successfully stored amenity data")
        except Exception as e:
            _logger.warning(f"Failed to store amenity data: {str(e)}")
            cr.execute("ROLLBACK")
            cr.execute("BEGIN")

    # Store specifications
    specs_to_store = {
        'passenger_capacity': {'code': 'load.passengers', 'category': 'load'},
        'range_nm': {'code': 'performance.range', 'category': 'performance'},
        'cruise_speed': {'code': 'performance.cruise_speed', 'category': 'performance'},
        'cabin_length': {'code': 'cabin.length', 'category': 'dimensions'},
        'cabin_width': {'code': 'cabin.width', 'category': 'dimensions'},
        'cabin_height': {'code': 'cabin.height', 'category': 'dimensions'},
        'luggage_capacity': {'code': 'load.luggage', 'category': 'load'},
        'useful_load': {'code': 'load.useful_load', 'category': 'load'},
    }

    for old_field, spec_info in specs_to_store.items():
        if column_exists(cr, 'flight_aircraft', old_field):
            _logger.info(f"Storing {old_field} data for migration to {spec_info['code']}")
            try:
                cr.execute(f"""
                    INSERT INTO website_fleet_migration (
                        aircraft_id, 
                        data_type, 
                        name, 
                        float_value,
                        category_name
                    )
                    SELECT 
                        id, 
                        'spec', 
                        %s, 
                        {old_field},
                        %s
                    FROM flight_aircraft 
                    WHERE {old_field} IS NOT NULL
                """, (spec_info['code'], spec_info['category']))
            except Exception as e:
                _logger.warning(f"Failed to store {old_field} data: {str(e)}")
                cr.execute("ROLLBACK")
                cr.execute("BEGIN")

    # Drop old columns safely
    old_fields = [
        'passenger_capacity', 'range_nm', 'cruise_speed', 
        'cabin_length', 'cabin_width', 'cabin_height',
        'luggage_capacity', 'useful_load',
        # Content fields that will be replaced by website_description
        'hero_content', 'spec_header_content', 'interior_gallery_header_content',
        'benefits_content', 'faq_header_content', 'faq_content',
        'main_carousel_content', 'interior_gallery_carousel_content', 'cta_content'
    ]

    for field in old_fields:
        if column_exists(cr, 'flight_aircraft', field):
            _logger.info(f"Dropping column {field}")
            try:
                cr.execute(f"ALTER TABLE flight_aircraft DROP COLUMN IF EXISTS {field}")
            except Exception as e:
                _logger.warning(f"Failed to drop column {field}: {str(e)}")
                cr.execute("ROLLBACK")
                cr.execute("BEGIN")

    # Drop amenity tables safely in correct order
    for table in [rel_table, amenity_table]:
        if table_exists(cr, table):
            _logger.info(f"Dropping table {table}")
            try:
                cr.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            except Exception as e:
                _logger.warning(f"Failed to drop table {table}: {str(e)}")
                cr.execute("ROLLBACK")
                cr.execute("BEGIN")

    _logger.info("Completed pre-migration")