# post-migration.py
from odoo.upgrade import util
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    if not version:
        return

    _logger.info("Starting website_flight_fleet post-migration")

    env = util.env(cr)

    # Get admin user for creating specs
    cr.execute("SELECT res_users.id FROM res_users WHERE login='admin' LIMIT 1")
    user_id = cr.fetchone()[0]

    # Helper function to create specs safely
    def create_spec(aircraft_id, code, value, user_id):
        try:
            util.logged_query(
                cr, """
                INSERT INTO flight_aircraft_spec (
                    aircraft_id, code_id, value_float, value_bool,
                    create_uid, create_date, write_uid, write_date
                )
                VALUES (
                    %s,
                    (SELECT id FROM flight_aircraft_spec_code WHERE code = %s),
                    %s, %s,
                    %s, now(), %s, now()
                )
                """, (aircraft_id, code, value if not isinstance(value, bool) else None, 
                      value if isinstance(value, bool) else None, user_id, user_id)
            )
        except Exception as e:
            _logger.error(f"Error creating spec for aircraft {aircraft_id}, code {code}: {e}")

    # 1. Migrate stored specifications to new spec system
    _logger.info("Starting specification migration")
    spec_codes = {
        'load.passengers': 'spec_passenger_capacity',
        'performance.range': 'spec_range',
        'performance.cruise_speed': 'spec_cruise_speed',
        'cabin.length': 'spec_cabin_length',
        'cabin.width': 'spec_cabin_width',
        'cabin.height': 'spec_cabin_height',
        'load.luggage': 'spec_luggage_capacity',
        'load.useful_load': 'spec_useful_load'
    }

    for spec_code in spec_codes:
        _logger.info(f"Migrating {spec_code} specifications")
        util.logged_query(
            cr, """
            SELECT SUBSTRING(p.res_id FROM 'flight.aircraft,([0-9]+)')::integer as aircraft_id,
                   p.value_float
            FROM ir_property p
            WHERE p.name LIKE 'temp_spec_' || %s || '%%'
            """, (spec_code,)
        )
        for aircraft_id, value in cr.fetchall():
            create_spec(aircraft_id, spec_code, value, user_id)

    # 2. Migrate amenities to specs
    _logger.info("Migrating amenities to specification system")
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

    util.logged_query(
        cr, """
        SELECT DISTINCT SUBSTRING(p.res_id FROM 'flight.aircraft,([0-9]+)')::integer as aircraft_id,
               p.value_text
        FROM ir_property p
        WHERE p.name LIKE 'temp_amenity_%'
        """
    )
    
    for aircraft_id, amenity_name in cr.fetchall():
        if amenity_name in amenity_codes:
            create_spec(aircraft_id, amenity_codes[amenity_name], True, user_id)

    # 3. Migrate HTML content to website_description
    _logger.info("Migrating HTML content to website_description")
    util.logged_query(
        cr, """
        UPDATE flight_aircraft a
        SET website_description = COALESCE(website_description, '') || p.value_text
        FROM ir_property p
        WHERE p.name = 'temp_html_content_' || a.id
        """
    )

    # 4. Clean up temporary data
    _logger.info("Cleaning up temporary migration data")
    util.logged_query(cr, """
        DELETE FROM ir_property 
        WHERE name LIKE 'temp_spec_%' 
           OR name LIKE 'temp_amenity_%'
           OR name LIKE 'temp_html_content_%'
    """)