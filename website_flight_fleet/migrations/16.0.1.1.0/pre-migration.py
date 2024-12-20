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

    # 1. First migrate all amenity data
    rel_table = 'flight_aircraft_amenity_rel'
    amenity_table = 'flight_aircraft_amenity'

    # Check tables existence with logging
    rel_exists = table_exists(cr, rel_table)
    amenity_exists = table_exists(cr, amenity_table)
    _logger.info(f"Checking amenity tables: rel_table exists: {rel_exists}, amenity_table exists: {amenity_exists}")

    if rel_exists and amenity_exists:
        _logger.info("Found amenity tables, checking columns")
        
        # Check if tables have data
        cr.execute(f"SELECT COUNT(*) FROM {amenity_table}")
        amenity_count = cr.fetchone()[0]
        cr.execute(f"SELECT COUNT(*) FROM {rel_table}")
        rel_count = cr.fetchone()[0]
        _logger.info(f"Found {amenity_count} amenities and {rel_count} relationships")
        
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
                    COALESCE(t.value, a.name), 
                    true,
                    a.sequence
                FROM {rel_table} rel
                JOIN {amenity_table} a ON rel.amenity_id = a.id
                LEFT JOIN ir_translation t ON (
                    t.name = 'flight.aircraft.amenity,name'
                    AND t.res_id = a.id
                    AND t.lang = 'en_US'
                    AND t.type = 'model'
                    AND t.state = 'translated'
                )
            """)
            
            # Verify data was inserted
            cr.execute("""
                SELECT COUNT(*) 
                FROM website_fleet_migration 
                WHERE data_type = 'amenity'
            """)
            migrated_count = cr.fetchone()[0]
            _logger.info(f"Successfully stored {migrated_count} amenity records")
            
        except Exception as e:
            _logger.warning(f"Failed to store amenity data: {str(e)}")
            cr.execute("ROLLBACK")
            cr.execute("BEGIN")
            return  # Stop migration if we can't store amenity data
    else:
        _logger.warning("Amenity tables not found, skipping amenity migration")

    # 2. Then migrate all specification data
    specs_to_store = {
        'passenger_capacity': {'code': 'load.passengers', 'category': 'load'},
        'range_nm': {'code': 'performance.range', 'category': 'performance'},
        'cruise_speed': {'code': 'performance.cruise_speed', 'category': 'performance'},
        'cabin_length': {'code': 'cabin.length', 'category': 'cabin'},
        'cabin_width': {'code': 'cabin.width', 'category': 'cabin'},
        'cabin_height': {'code': 'cabin.height', 'category': 'cabin'},
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
                return  # Stop migration if we can't store spec data

    # Verify all data is migrated
    cr.execute("SELECT data_type, COUNT(*) FROM website_fleet_migration GROUP BY data_type")
    counts = cr.fetchall()
    _logger.info(f"Migration table contents: {counts}")

    # 3. Only after successful migration, drop old data
    # Drop old columns safely
    old_fields = [
        'passenger_capacity', 'range_nm', 'cruise_speed', 
        'cabin_length', 'cabin_width', 'cabin_height',
        'luggage_capacity', 'useful_load',
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

    # Finally drop amenity tables
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