# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import base64
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FlightDataImportMixin(models.AbstractModel):
    """Mixin for flight data import wizards.
    
    This mixin provides common functionality for all data import wizards in the flight module,
    similar to the account.statement.import model in the bank-statement-import module.
    
    It can be used for importing flights, aircraft, pilots, or any other data in the flight module.
    """
    _name = "flight.data.import.mixin"
    _description = "Flight Data Import Mixin"

    # File import fields
    import_file = fields.Binary(
        string="Import File",
        required=True,
        help="Select a file to import",
    )
    filename = fields.Char("Filename")
    
    # Import state tracking
    state = fields.Selection([
        ('draft', 'Draft'),
        ('preview', 'Preview'),
        ('done', 'Imported')
    ], default='draft', string="Import State")
    
    # Statistics
    total_rows = fields.Integer("Total Rows", readonly=True)
    valid_rows = fields.Integer("Valid Rows", readonly=True)
    invalid_rows = fields.Integer("Invalid Rows", readonly=True)
    conflict_rows = fields.Integer("Conflict Rows", readonly=True)
    
    # Conflict resolution
    update_existing = fields.Boolean(
        "Update Existing Records", 
        default=True,
        help="If checked, existing aircraft and pilots will be updated with imported data"
    )
    
    # Common methods
    def _import_file(self):
        """Process the file and prepare data for preview.
        
        This method is similar to the _import_file method in account.statement.import.
        It processes the uploaded file and prepares the data for preview.
        
        Returns:
            dict: Result of the import process
        """
        self.ensure_one()
        result = {
            "imported_ids": [],
            "notifications": [],  # list of text messages
        }
        
        _logger.info("Start to import file %s", self.filename)
        file_data = base64.b64decode(self.import_file)
        
        # Parse the file
        try:
            self.import_single_file(file_data, result)
        except Exception as e:
            raise UserError(f"Error importing file: {str(e)}")
            
        return result
    
    def action_import_file(self):
        """Process the file chosen in the wizard and return an action.
        
        This method is similar to the import_file_button method in account.statement.import.
        It processes the uploaded file and returns an action to display the results.
        
        Returns:
            dict: Action to display import results
        """
        result = self._import_file()
        
        # Update statistics
        self._update_statistics()
        
        # Update state
        self.state = 'preview'
        
        # Return view
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
    
    def import_single_file(self, file_data, result):
        """Import a single file.
        
        This method should be implemented by specific import wizards.
        It should parse the file and create import lines.
        
        Args:
            file_data (bytes): The file content
            result (dict): Dictionary to store import results
        """
        raise NotImplementedError("This method must be implemented by specific import wizards")
    
    def _parse_file(self, file_data):
        """Parse the file content.
        
        This method should be implemented by specific import wizards.
        It should return a dictionary with the parsed data.
        
        Args:
            file_data (bytes): The file content
            
        Returns:
            dict: Parsed data
        """
        raise NotImplementedError("This method must be implemented by specific import wizards")
    
    def _reset_statistics(self):
        """Reset import statistics."""
        self.write({
            'total_rows': 0,
            'valid_rows': 0,
            'invalid_rows': 0,
            'conflict_rows': 0,
        })
    
    def _update_statistics(self):
        """Update import statistics based on import lines.
        
        This method should be implemented by specific import wizards.
        It should update the statistics based on the import lines.
        """
        pass
    
    def _check_parsed_data(self, data):
        """Check if the parsed data is valid.
        
        This method is similar to the _check_parsed_data method in account.statement.import.
        It performs basic validation on the parsed data.
        
        Args:
            data (dict): Parsed data
            
        Returns:
            bool: True if the data is valid, False otherwise
        """
        if not data or not isinstance(data, dict):
            return False
            
        if 'rows' not in data or not data['rows']:
            return False
            
        return True
    
    def _show_error(self, message):
        """Show error message to user."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Error',
                'message': message,
                'sticky': True,
                'type': 'danger',
            }
        }
    
    def _show_success(self, message):
        """Show success message to user."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Success',
                'message': message,
                'sticky': False,
                'type': 'success',
            }
        }
        
    def _prepare_create_attachment(self, result, model, res_id):
        """Prepare values for creating an attachment.
        
        This method is similar to the _prepare_create_attachment method in account.statement.import.
        It prepares values for creating an attachment for the imported file.
        
        Args:
            result (dict): Import result
            model (str): Target model
            res_id (int): ID of the record to attach to
            
        Returns:
            dict: Values for creating an attachment
        """
        return {
            'name': self.filename,
            'res_id': res_id,
            'res_model': model,
            'datas': self.import_file,
        }


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
