# post-migration.py
import logging
import json

_logger = logging.getLogger(__name__)

def create_spec(cr, aircraft_id, code, value, user_id, is_bool=False):
    try:
        # Log attempt to create spec
        _logger.info(f"Attempting to create spec - Aircraft: {aircraft_id}, Code: {code}, Value: {value}, Is Bool: {is_bool}")

        # Check if spec already exists
        cr.execute("""
            SELECT id FROM flight_aircraft_spec 
            WHERE aircraft_id = %s 
            AND code_id = (SELECT id FROM flight_aircraft_spec_code WHERE code = %s)
        """, (aircraft_id, code))
        
        if cr.fetchone():
            _logger.info(f"Spec already exists for aircraft {aircraft_id}, code {code}")
            return

        # Get the spec code record to determine type and default UOM
        cr.execute("""
            SELECT id, code_type, default_uom_id 
            FROM flight_aircraft_spec_code 
            WHERE code = %s
        """, (code,))
        spec_code = cr.fetchone()
        if not spec_code:
            _logger.warning(f"Spec code {code} not found in flight_aircraft_spec_code")
            return

        spec_code_id, code_type, default_uom_id = spec_code
        _logger.info(f"Found spec code - ID: {spec_code_id}, Type: {code_type}, Default UOM: {default_uom_id}")

        # Prepare values based on type
        value_bool = value if is_bool else None
        value_float = None if is_bool else value
        value_text = None

        # Create spec with proper UOM
        cr.execute("""
            INSERT INTO flight_aircraft_spec (
                aircraft_id, code_id, value_float, value_bool, value_text,
                uom_id, create_uid, create_date, write_uid, write_date
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, now(), %s, now()
            )
            RETURNING id
        """, (
            aircraft_id, spec_code_id, value_float, value_bool, value_text,
            default_uom_id, user_id, user_id
        ))
        
        new_spec_id = cr.fetchone()[0]
        _logger.info(f"Successfully created spec with ID: {new_spec_id}")
        
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

    # Get superuser/admin ID - more reliable method
    cr.execute("SELECT MIN(id) FROM res_users WHERE id = 1")
    user_id = cr.fetchone()
    if not user_id:
        _logger.error("Could not determine admin user ID, aborting migration")
        return
    user_id = user_id[0]

    # Migrate specifications
    _logger.info("Migrating specifications")
    cr.execute("""
        SELECT aircraft_id, name, float_value
        FROM website_fleet_migration
        WHERE data_type = 'spec' AND float_value IS NOT NULL
    """)
    specs = cr.fetchall()
    _logger.info(f"Found {len(specs)} specifications to migrate")
    for aircraft_id, code, value in specs:
        create_spec(cr, aircraft_id, code, value, user_id)

    # Migrate amenities
    amenity_codes = {
        'Starlink WiFi': 'amenity.wifi',
        'Power Outlets': 'amenity.power',
        'Quiet Cabin': 'amenity.quiet_cabin',
        'Enclosed Aft Lavatory': 'amenity.lavatory',
        'Air Conditioning': 'amenity.air_conditioning',
        'Leather Seats': 'amenity.leather_seats',
        'Entertainment System': 'amenity.entertainment',
        'Refreshment Center': 'amenity.refreshments',
        'Cargo Door': 'amenity.cargo_door'
    }

    _logger.info("Migrating amenities")
    cr.execute("""
        SELECT DISTINCT aircraft_id, name
        FROM website_fleet_migration
        WHERE data_type = 'amenity'
    """)
    amenities = cr.fetchall()
    _logger.info(f"Found {len(amenities)} amenities to migrate")
    
    # Verify amenity spec codes exist
    cr.execute("""
        SELECT code, id FROM flight_aircraft_spec_code 
        WHERE code IN %s
    """, (tuple(amenity_codes.values()),))
    existing_codes = cr.fetchall()
    _logger.info(f"Found {len(existing_codes)} existing amenity spec codes: {[code[0] for code in existing_codes]}")

    for aircraft_id, amenity_name in amenities:
        if amenity_name in amenity_codes:
            code = amenity_codes[amenity_name]
            _logger.info(f"Processing amenity {amenity_name} -> {code} for aircraft {aircraft_id}")
            create_spec(cr, aircraft_id, code, True, user_id, is_bool=True)

    # Fix null UOMs using default UOMs from spec codes
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
    updated_uoms = cr.fetchall()
    _logger.info(f"Updated UOMs for {len(updated_uoms)} specifications")

    # Set default website description
    _logger.info("Setting default website description")
    default_content = {
        "en_US": '''
<section class="container mt-7 mb-2 text-center">
    <div class="mw-100 mw-lg-50 mx-auto">
        <div class="o_animate o_anim_slide_in o_anim_from_bottom" style="--wanim-intensity: 20; animation-duration: 0.4s;">
            <h2 class="fw-bold text-black text-center mb-4">Aircraft Showcase</h2>
            <p class="lead text-black">Explore our stunning aircraft interiors.</p>
        </div>
    </div>
</section>
<section class="py-7">
    <div class="container">
        <div class="row g-5">
            <div class="col-lg-6">
                <div class="benefit-item">
                    <div class="mb-4">
                        <h4 class="fw-bold">Enhanced Performance and Versatility</h4>
                    </div>
                    <p>Discover exceptional versatility with advanced avionics and proven reliability. 
                    This aircraft delivers outstanding performance across various mission profiles.</p>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="benefit-item">
                    <div class="mb-4">
                        <h4 class="fw-bold">Premium Comfort</h4>
                    </div>
                    <p>Experience unmatched comfort with our meticulously maintained cabin. 
                    Every detail is designed for your optimal travel experience.</p>
                </div>
            </div>
        </div>
    </div>
</section>'''
    }
    
    # Convert to JSON string
    default_content_json = json.dumps(default_content)
    
    cr.execute("""
        SELECT id, website_description 
        FROM flight_aircraft 
        WHERE website_description IS NULL
    """)
    null_descriptions = cr.fetchall()
    _logger.info(f"Found {len(null_descriptions)} aircraft without website description")

    if null_descriptions:
        cr.execute("""
            UPDATE flight_aircraft 
            SET website_description = %s::jsonb 
            WHERE website_description IS NULL
        """, (default_content_json,))
        _logger.info("Updated website descriptions with default content")

        # Verify the update
        cr.execute("SELECT COUNT(*) FROM flight_aircraft WHERE website_description IS NULL")
        remaining_null = cr.fetchone()[0]
        _logger.info(f"Remaining aircraft with null website description: {remaining_null}")

    # Drop temporary table
    _logger.info("Cleaning up migration table")
    cr.execute("DROP TABLE IF EXISTS website_fleet_migration")

    _logger.info("Completed post-migration")