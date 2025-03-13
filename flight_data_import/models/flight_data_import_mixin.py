# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import logging

from odoo import fields, models, _

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
        help="If checked, existing records will be updated with imported data"
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
        """Update import statistics based on import lines."""
        raise NotImplementedError("This method must be implemented by specific import wizards")
    
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
    
    def _process_parsed_data(self, parsed_data, result):
        """Process the parsed data and create import lines.
        
        This method should be implemented by specific import wizards.
        It should process the parsed data and create import lines.
        
        Args:
            parsed_data (dict): Parsed data with header and rows
            result (dict): Dictionary to store import results
        """
        raise NotImplementedError("This method must be implemented by specific import wizards")
    
    def _get_import_line_model(self):
        """Get the model name for import lines.
        
        This method should be implemented by specific import wizards.
        
        Returns:
            str: Model name for import lines
        """
        raise NotImplementedError("This method must be implemented by specific import wizards")
    
    def _get_default_field_mapping(self):
        """Get default field mapping for the import file format.
        
        This method should be implemented by specific import wizards.
        
        Returns:
            dict: Mapping of column indices to field names
        """
        raise NotImplementedError("This method must be implemented by specific import wizards")
    
    def _show_error(self, message):
        """Show an error message to the user."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Error'),
                'message': message,
                'sticky': False,
                'type': 'danger',
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': self._name,
                    'res_id': self.id,
                    'view_mode': 'form',
                    'views': [[False, 'form']],
                    'target': 'new',
                },
            }
        }
    
    def _show_success(self, message):
        """Show a success message to the user."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': message,
                'sticky': False,
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': self._name,
                    'res_id': self.id,
                    'view_mode': 'form',
                    'views': [[False, 'form']],
                    'target': 'new',
                },
            }
        }
    
    def action_import(self):
        """Import the selected lines.
        
        This method provides a standard implementation for importing lines.
        It can be overridden by specific import wizards if needed.
        """
        self.ensure_one()
        
        # Get lines to import based on state
        lines_to_import = self._get_lines_to_import()
        
        if not lines_to_import:
            return self._show_error(_("No valid lines to import."))
        
        stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
        }
        
        imported_ids = []
        for line in lines_to_import:
            try:
                record_id = line.action_import()
                if record_id:
                    imported_ids.append(record_id)
                    if line.state == "imported":
                        if getattr(line, 'is_new', True):
                            stats["created"] += 1
                        else:
                            stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                _logger.exception("Error importing line %s", line.id)
                line.mark_as_invalid(str(e))
                stats["failed"] += 1
        
        # Update statistics after import
        self._update_statistics()
        
        # Update state if all lines are imported
        if all(line.state == 'imported' or line.state == 'invalid' 
               for line in self._get_all_import_lines()):
            self.state = 'done'
        
        # Show success message
        message = _(
            "Import completed: "
            "Created: %(created)s "
            "Updated: %(updated)s "
            "Skipped: %(skipped)s "
            "Failed: %(failed)s"
        ) % stats
        
        return self._show_success(message)
    
    def _get_lines_to_import(self):
        """Get lines to import based on state.
        
        This method should be implemented by specific import wizards.
        
        Returns:
            recordset: Lines to import
        """
        raise NotImplementedError("This method must be implemented by specific import wizards")
    
    def _get_all_import_lines(self):
        """Get all import lines.
        
        This method should be implemented by specific import wizards.
        
        Returns:
            recordset: All import lines
        """
        raise NotImplementedError("This method must be implemented by specific import wizards")
