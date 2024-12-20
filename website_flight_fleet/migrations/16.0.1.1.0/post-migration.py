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

    # Define amenity mapping with lowercase keys
    amenity_codes = {
        'starlink wifi': 'amenity.wifi',
        'power outlets': 'amenity.power',
        'quiet cabin': 'amenity.quiet_cabin',
        'enclosed aft lavatory': 'amenity.lavatory',
        'air conditioning': 'amenity.air_conditioning',
        'leather seats': 'amenity.leather_seats',
        'entertainment system': 'amenity.entertainment',
        'refreshment center': 'amenity.refreshments',
        'cargo door': 'amenity.cargo_door',
        'coffee maker': 'amenity.coffee_maker',
        'ice drawer': 'amenity.ice_drawer',
        'microwave & oven': 'amenity.microwave_oven',
        'cabin environment control': 'amenity.cabin_environment_control'
    }

    # Migrate amenities
    _logger.info("Migrating amenities")
    cr.execute("""
        SELECT DISTINCT aircraft_id, name
        FROM website_fleet_migration
        WHERE data_type = 'amenity'
    """)
    amenities = cr.fetchall()
    _logger.info(f"Found {len(amenities)} amenities to migrate")

    # Create specs for amenities
    for aircraft_id, amenity_name in amenities:
        # Convert to lowercase for case-insensitive comparison
        amenity_name_lower = amenity_name.lower()
        if amenity_name_lower in amenity_codes:
            code = amenity_codes[amenity_name_lower]
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