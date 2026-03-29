# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Update Uzbekistan airport ICAO codes from UT prefix to UZ prefix.

    Starting 2 October 2025, all airports in Uzbekistan officially changed their
    ICAO location indicators from the "UT" prefix to "UZ" to better reflect the
    national identity, replacing Soviet-era codes.
    """
    _logger.info(
        "Starting migration: Update Uzbekistan ICAO codes from UT to UZ prefix"
    )

    # Update ICAO codes: replace 'UT' prefix with 'UZ' for Uzbekistan aerodromes
    cr.execute(
        """
        UPDATE flight_aerodrome
        SET icao = 'UZ' || substring(icao from 3)
        WHERE icao LIKE 'UT%%'
          AND country_id = (SELECT id FROM res_country WHERE code = 'UZ')
        """
    )
    _logger.info("Updated %d aerodrome ICAO codes from UT to UZ prefix", cr.rowcount)

    # Update corresponding XML IDs to match the new ICAO codes
    cr.execute(
        """
        UPDATE ir_model_data
        SET name = 'aerodrome_UZ' || substring(name from 13)
        WHERE name LIKE 'aerodrome\_UT%%'
          AND model = 'flight.aerodrome'
          AND res_id IN (
              SELECT id FROM flight_aerodrome
              WHERE country_id = (SELECT id FROM res_country WHERE code = 'UZ')
          )
        """
    )
    _logger.info("Updated %d aerodrome XML IDs from UT to UZ prefix", cr.rowcount)

    _logger.info(
        "Migration completed: Uzbekistan ICAO codes updated from UT to UZ prefix"
    )
