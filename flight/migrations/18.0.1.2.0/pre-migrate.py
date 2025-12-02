# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Rename flight.crew model to flight.flight.crew

    This migration renames the model name in ir_model and related tables
    while keeping the database table name as flight_crew for data compatibility.
    """
    _logger.info("Starting migration: Rename flight.crew to flight.flight.crew")

    # Update ir_model table - rename model name
    cr.execute("""
        UPDATE ir_model
        SET model = 'flight.flight.crew'
        WHERE model = 'flight.crew'
    """)
    _logger.info("Updated ir_model: flight.crew -> flight.flight.crew")

    # Update ir_model_data table - update model references
    cr.execute("""
        UPDATE ir_model_data
        SET model = 'flight.flight.crew'
        WHERE model = 'flight.crew'
    """)
    _logger.info("Updated ir_model_data references")

    # Update ir_model_fields table - update model references
    cr.execute("""
        UPDATE ir_model_fields
        SET model = 'flight.flight.crew'
        WHERE model = 'flight.crew'
    """)
    _logger.info("Updated ir_model_fields references")

    # Update ir_model_fields table - update relation references
    cr.execute("""
        UPDATE ir_model_fields
        SET relation = 'flight.flight.crew'
        WHERE relation = 'flight.crew'
    """)
    _logger.info("Updated ir_model_fields relations")

    # Update ir_model_access table - update model references
    cr.execute("""
        UPDATE ir_model_access
        SET model_id = (SELECT id FROM ir_model WHERE model = 'flight.flight.crew')
        WHERE model_id = (SELECT id FROM ir_model WHERE model = 'flight.crew')
    """)
    _logger.info("Updated ir_model_access references")

    # Update ir_rule table - update model references
    cr.execute("""
        UPDATE ir_rule
        SET model_id = (SELECT id FROM ir_model WHERE model = 'flight.flight.crew')
        WHERE model_id IN (SELECT id FROM ir_model WHERE model = 'flight.crew')
    """)
    _logger.info("Updated ir_rule references")

    # Update ir_ui_view table - update model references in views
    cr.execute("""
        UPDATE ir_ui_view
        SET model = 'flight.flight.crew'
        WHERE model = 'flight.crew'
    """)
    _logger.info("Updated ir_ui_view model references")

    # Update ir_act_window table - update res_model references in actions
    cr.execute("""
        UPDATE ir_act_window
        SET res_model = 'flight.flight.crew'
        WHERE res_model = 'flight.crew'
    """)
    _logger.info("Updated ir_act_window res_model references")

    _logger.info("Migration completed: flight.crew renamed to flight.flight.crew")
