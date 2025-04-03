import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migration script to handle duplicate flight crew roles.

    This script:
    1. Detects duplicate flight crew roles based on name
    2. For each duplicate set, keeps the record with the lowest ID (oldest)
    3. Checks if newer duplicates are associated with locked flights
    4. Removes duplicates that aren't associated with locked flights
    5. Makes duplicates inactive if they can't be removed due to locked flights
    """
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})

    _logger.info("Starting migration to handle duplicate flight crew roles")

    # Get all flight crew roles ordered by ID (oldest first)
    roles = env["flight.crew.role"].search([], order="id")

    if not roles:
        _logger.info("No flight crew roles found, nothing to migrate")
        return

    _logger.info("Found %d flight crew roles to analyze", len(roles))

    # Dictionary to track unique roles by name and their first occurrence
    unique_roles = {}
    duplicates = []

    # Identify duplicates (keeping the one with lowest ID - oldest record)
    for role in roles:
        if role.name in unique_roles:
            # This is a duplicate, add to duplicates list
            duplicates.append(
                {
                    "id": role.id,
                    "name": role.name,
                    "original_id": unique_roles[role.name],
                }
            )
            _logger.info(
                'Found duplicate role "%s" (ID: %d), original has ID: %d',
                role.name,
                role.id,
                unique_roles[role.name],
            )
        else:
            # First time seeing this role name
            unique_roles[role.name] = role.id
            _logger.info('Keeping original role "%s" (ID: %d)', role.name, role.id)

    if not duplicates:
        _logger.info("No duplicate roles found, nothing to migrate")
        return

    _logger.info("Found %d duplicate roles to handle", len(duplicates))

    # Check if flight_crew has a lock_state field to identify locked flights
    has_lock_field = False
    cr.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_name = 'flight' AND column_name = 'lock_state'"
    )
    if cr.fetchone():
        has_lock_field = True
        _logger.info("Flight model has lock_state field, will check for locked flights")

    # Check if flight.crew.role has active field
    has_active_field = False
    cr.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_name = 'flight_crew_role' AND column_name = 'active'"
    )
    if cr.fetchone():
        has_active_field = True
        _logger.info(
            "flight.crew.role model has active field, will use it for duplicates that cannot be removed"
        )

    # Process each duplicate
    safe_to_remove = []
    cannot_remove = []

    for duplicate in duplicates:
        dup_id = duplicate["id"]

        # Check if this duplicate is used in any flight crew
        cr.execute("SELECT COUNT(*) FROM flight_crew WHERE role_id = %s", (dup_id,))
        crew_count = cr.fetchone()[0]

        if crew_count == 0:
            # Not used in any flight crew, safe to remove
            safe_to_remove.append(dup_id)
            _logger.info(
                'Role "%s" (ID: %d) is not used in any flight crew, safe to remove',
                duplicate["name"],
                dup_id,
            )
            continue

        # Check if used in locked flights
        if has_lock_field:
            cr.execute(
                """
                SELECT COUNT(*) FROM flight_crew fc
                JOIN flight f ON fc.flight_id = f.id
                WHERE fc.role_id = %s AND f.lock_state = 'locked'
            """,
                (dup_id,),
            )
            locked_count = cr.fetchone()[0]

            if locked_count == 0:
                # Used in flights but none are locked, update references and remove
                safe_to_remove.append(dup_id)

                # Update references to point to the original role
                original_id = duplicate["original_id"]
                cr.execute(
                    "UPDATE flight_crew SET role_id = %s WHERE role_id = %s",
                    (original_id, dup_id),
                )

                _logger.info(
                    "Updated %d flight crew records from role ID %d to %d",
                    crew_count,
                    dup_id,
                    original_id,
                )
            else:
                # Used in locked flights, cannot remove
                cannot_remove.append(dup_id)
                _logger.info(
                    'Role "%s" (ID: %d) is used in %d locked flights, cannot remove',
                    duplicate["name"],
                    dup_id,
                    locked_count,
                )
        else:
            # Cannot determine if flights are locked, assume cannot remove
            cannot_remove.append(dup_id)
            _logger.info(
                'Role "%s" (ID: %d) is used in flights and lock status cannot be determined, cannot remove',
                duplicate["name"],
                dup_id,
            )

    # Remove duplicates that are safe to remove
    if safe_to_remove:
        ids_str = ",".join(map(str, safe_to_remove))
        cr.execute(f"DELETE FROM flight_crew_role WHERE id IN ({ids_str})")
        _logger.info("Successfully removed %d duplicate roles", len(safe_to_remove))

    # Make duplicates inactive if they cannot be removed but have active field
    if cannot_remove and has_active_field:
        ids_str = ",".join(map(str, cannot_remove))
        cr.execute(
            f"UPDATE flight_crew_role SET active = false WHERE id IN ({ids_str})"
        )
        _logger.info(
            "Set %d duplicate roles as inactive (used in locked flights)",
            len(cannot_remove),
        )

    # Log completion
    _logger.info(
        "Migration completed. Removed %d duplicates, made %d inactive.",
        len(safe_to_remove),
        len(cannot_remove) if has_active_field else 0,
    )
