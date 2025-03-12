# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class FlightDataImportLineMixin(models.AbstractModel):
    """Mixin for flight data import lines.
    
    This mixin provides common functionality for all data import lines in the flight module.
    It can be used for importing flights, aircraft, pilots, or any other data.
    """
    _name = "flight.data.import.line.mixin"
    _description = "Flight Data Import Line Mixin"

    # Common fields for all import lines
    state = fields.Selection([
        ('draft', 'Draft'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('conflict', 'Conflict'),
        ('imported', 'Imported'),
    ], default='draft', string="Status")
    
    error_message = fields.Text("Error Message")
    warning_message = fields.Text("Warning Message")
    
    # Raw data fields
    raw_data = fields.Text("Raw Data", help="Original data from the import file")
    
    # Selection for import
    to_import = fields.Boolean("Import", default=True, 
                              help="Select to import this record")
    
    # Common methods
    def validate(self):
        """Validate the import line.
        
        This method should be implemented by specific import line models.
        It should validate the line data and update the state accordingly.
        
        Returns:
            bool: True if the line is valid, False otherwise
        """
        raise NotImplementedError("This method must be implemented by specific import line models")
    
    def prepare_import_values(self):
        """Prepare values for import.
        
        This method should be implemented by specific import line models.
        It should return a dictionary with values for creating the target record.
        
        Returns:
            dict: Values for creating/updating the target record
        """
        raise NotImplementedError("This method must be implemented by specific import line models")
    
    def check_conflicts(self):
        """Check for conflicts with existing records.
        
        This method should be implemented by specific import line models.
        It should check if the line conflicts with existing records.
        
        Returns:
            tuple: (has_conflict, conflict_record_id, conflict_message)
        """
        raise NotImplementedError("This method must be implemented by specific import line models")
    
    def mark_as_valid(self):
        """Mark the line as valid."""
        self.write({
            'state': 'valid',
            'error_message': False,
        })
    
    def mark_as_invalid(self, error_message):
        """Mark the line as invalid with an error message."""
        self.write({
            'state': 'invalid',
            'error_message': error_message,
            'to_import': False,
        })
    
    def mark_as_conflict(self, conflict_message, to_import=False):
        """Mark the line as conflicting with an existing record."""
        self.write({
            'state': 'conflict',
            'warning_message': conflict_message,
            'to_import': to_import,
        })
    
    def mark_as_imported(self):
        """Mark the line as imported."""
        self.write({
            'state': 'imported',
        })
