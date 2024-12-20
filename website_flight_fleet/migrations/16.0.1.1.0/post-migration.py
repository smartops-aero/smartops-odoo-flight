# post-migration.py
import logging

_logger = logging.getLogger(__name__)

def create_spec(cr, aircraft_id, code, value, user_id, is_bool=False, category_id=None):
    """Create a specification for an aircraft"""
    try:
        # Check if spec already exists
        cr.execute("""
            SELECT id FROM flight_aircraft_spec 
            WHERE aircraft_id = %s 
            AND code_id = (SELECT id FROM flight_aircraft_spec_code WHERE code = %s)
        """, (aircraft_id, code))
        
        if cr.fetchone():
            _logger.info(f"Spec already exists for aircraft {aircraft_id}, code {code}")
            return

        # Get or create spec code
        cr.execute("""
            SELECT id, code_type, default_uom_id 
            FROM flight_aircraft_spec_code 
            WHERE code = %s
        """, (code,))
        spec_code = cr.fetchone()
        
        if not spec_code:
            _logger.info(f"Creating spec code {code}")
            # Split code to get name
            name = code.split('.')[-1].replace('_', ' ').title()
            code_type = 'boolean' if is_bool else 'float'
            
            cr.execute("""
                INSERT INTO flight_aircraft_spec_code 
                (code, name, code_type, category_id, create_uid, write_uid)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, code_type, default_uom_id
            """, (code, name, code_type, category_id, user_id, user_id))
            spec_code = cr.fetchone()

        spec_code_id, code_type, default_uom_id = spec_code

        # Prepare values based on type
        value_bool = value if is_bool else None
        value_float = None if is_bool else value
        value_text = None

        # Create spec with proper UOM
        cr.execute("""
            INSERT INTO flight_aircraft_spec (
                aircraft_id, code_id, value_float, value_bool, value_text,
                uom_id, create_uid, write_uid
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            aircraft_id, spec_code_id, value_float, value_bool, value_text,
            default_uom_id, user_id, user_id
        ))
        
        new_spec_id = cr.fetchone()[0]
        _logger.info(f"Created spec {new_spec_id} for aircraft {aircraft_id}, code {code}")
        
    except Exception as e:
        _logger.error(f"Error creating spec for aircraft {aircraft_id}, code {code}: {str(e)}")

def migrate(cr, version):
    if not version:
        return

    _logger.info("Starting website_flight_fleet post-migration")

    # Check for temporary table
    cr.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'website_fleet_migration')")
    if not cr.fetchone()[0]:
        _logger.error("Migration table not found, skipping post-migration")
        return

    # Get superuser ID
    cr.execute("SELECT MIN(id) FROM res_users WHERE id = 1")
    user_id = cr.fetchone()
    if not user_id:
        _logger.error("Could not determine admin user ID")
        return
    user_id = user_id[0]

    # Get or create spec categories
    categories = {
        'performance': 'Performance Specifications',
        'cabin': 'Cabin Capabilities',
        'load': 'Load Capabilities',
        'amenity': 'Amenities'
    }

    category_ids = {}
    for code, name in categories.items():
        cr.execute("""
            SELECT id FROM flight_aircraft_spec_category WHERE code = %s
        """, (code,))
        category_id = cr.fetchone()
        
        if not category_id:
            cr.execute("""
                INSERT INTO flight_aircraft_spec_category (code, name, create_uid, write_uid)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (code, name, user_id, user_id))
            category_id = cr.fetchone()
        
        category_ids[code] = category_id[0]

    # Migrate specifications
    _logger.info("Migrating specifications")
    cr.execute("""
        SELECT aircraft_id, name, float_value, category_name
        FROM website_fleet_migration
        WHERE data_type = 'spec' AND float_value IS NOT NULL
    """)
    specs = cr.fetchall()
    
    for aircraft_id, code, value, category in specs:
        category_id = category_ids.get(category)
        create_spec(cr, aircraft_id, code, value, user_id, category_id=category_id)

    # First check if we have any amenities in the temporary table
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'website_fleet_migration'
        )
    """)
    if not cr.fetchone()[0]:
        _logger.error("Migration table does not exist! Pre-migration might have failed.")
        return

    # Check what's in the temporary table
    cr.execute("""
        SELECT DISTINCT data_type, name 
        FROM website_fleet_migration
    """)
    temp_data = cr.fetchall()
    _logger.info(f"Data in temporary table: {temp_data}")

    # First gather all unique amenity names
    cr.execute("""
        SELECT DISTINCT name 
        FROM website_fleet_migration 
        WHERE data_type = 'amenity'
    """)
    old_amenity_names = [row[0] for row in cr.fetchall()]
    _logger.info(f"Found {len(old_amenity_names)} unique amenities to migrate: {old_amenity_names}")

    # Get all existing amenity spec codes
    cr.execute("""
        SELECT code, id, name 
        FROM flight_aircraft_spec_code 
        WHERE code LIKE 'amenity.%'
    """)
    rows = cr.fetchall()
    _logger.info(f"Found {len(rows)} amenity spec codes")
    
    spec_codes = {}
    for row in rows:
        code, id, name = row
        _logger.info(f"Processing row: code={code}, id={id}, name={type(name)}={name}")
        if isinstance(name, dict) and 'en_US' in name:  # Handle translated field
            spec_codes[name['en_US'].lower()] = (code, id)
        else:
            _logger.warning(f"Unexpected name format: {type(name)}={name}")

    # Create mapping and log unmapped amenities
    amenity_mapping = {}
    unmapped_amenities = []
    for old_name in old_amenity_names:
        if old_name:  # Check if old_name is not None
            old_name_lower = old_name.lower()
            if old_name_lower in spec_codes:
                amenity_mapping[old_name] = spec_codes[old_name_lower][0]
            else:
                unmapped_amenities.append(old_name)
                _logger.warning(f"Could not map amenity: {old_name}")

    if unmapped_amenities:
        _logger.warning(f"The following amenities could not be mapped: {', '.join(unmapped_amenities)}")

    # Migrate amenities using the mapping
    cr.execute("""
        SELECT aircraft_id, name
        FROM website_fleet_migration
        WHERE data_type = 'amenity'
    """)
    for aircraft_id, amenity_name in cr.fetchall():
        if amenity_name and amenity_name in amenity_mapping:
            code = amenity_mapping[amenity_name]
            create_spec(cr, aircraft_id, code, True, user_id, is_bool=True)

    # Fix null UOMs
    _logger.info("Fixing null UOMs")
    cr.execute("""
        UPDATE flight_aircraft_spec fas
        SET uom_id = fasc.default_uom_id
        FROM flight_aircraft_spec_code fasc
        WHERE fas.code_id = fasc.id
        AND fas.uom_id IS NULL
        AND fasc.default_uom_id IS NOT NULL
        RETURNING fas.id
    """)
    updated_specs = cr.fetchall()
    _logger.info(f"Updated UOMs for {len(updated_specs)} specifications")

    # Drop temporary table
    _logger.info("Cleaning up migration table")
    cr.execute("DROP TABLE IF EXISTS website_fleet_migration")

    _logger.info("Completed post-migration")