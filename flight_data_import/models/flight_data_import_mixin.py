# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class FlightDataImportMixin(models.AbstractModel):
    """Mixin for flight data import wizards.
    
    This mixin provides common functionality for all data import wizards in the flight module,
    similar to the account.statement.import model in the bank-statement-import module.
    
    It can be used for importing flights, aircraft, pilots, or any other data in the flight module.
    """
    _name = "flight.data.import.mixin"
    _description = "Flight Data Import Mixin"
    
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
        
        This is a template method that should be overridden by specific import wizards.
        The implementation should update the statistics fields based on the import result.
        
        Example implementation for a specific wizard:
        ```
        def _update_statistics(self):
            self.write({
                'total_rows': len(self.import_line_ids),
                'valid_rows': len(self.import_line_ids.filtered(lambda l: l.state == 'valid')),
                'invalid_rows': len(self.import_line_ids.filtered(lambda l: l.state == 'invalid')),
                'conflict_rows': len(self.import_line_ids.filtered(lambda l: l.state == 'conflict')),
            })
        ```
        """
        pass
    
    def action_reset(self):
        """Reset the import wizard to draft state."""
        self.ensure_one()
        self._reset_statistics()
        self.state = 'draft'
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
    
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
        """Show error message to user.
        
        Returns:
            dict: Action to display error notification
        """
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
        """Show success message to user.
        
        Returns:
            dict: Action to display success notification
        """
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
