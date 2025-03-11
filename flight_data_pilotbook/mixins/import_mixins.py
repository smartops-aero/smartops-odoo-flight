# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import api, fields, models


class ImportLineMixin(models.AbstractModel):
    """Mixin for import line models with common fields and methods."""

    _name = "flight.import.line.mixin"
    _description = "Import Line Mixin"

    # Status fields
    status = fields.Selection(
        [
            ("valid", "Valid"),
            ("invalid", "Invalid"),
            ("conflict", "Conflict"),
        ],
        default="valid",
        string="Status",
        help="Status of the import record",
    )
    message = fields.Text("Message", help="Message related to the import record")
    
    # Import selection
    to_import = fields.Boolean(
        default=True,
        string="Import",
        help="Whether this record should be imported",
    )
    
    # Result after import
    result = fields.Selection(
        [
            ("created", "Created"),
            ("updated", "Updated"),
            ("skipped", "Skipped"),
        ],
        string="Result",
        help="Result of the import process for this record",
    )
    
    @api.depends("status")
    def _compute_state_color(self):
        """Compute the color for the status badge."""
        for record in self:
            if record.status == "valid":
                record.state_color = "success"
            elif record.status == "invalid":
                record.state_color = "danger"
            elif record.status == "conflict":
                record.state_color = "warning"
            else:
                record.state_color = "secondary"
    
    state_color = fields.Char(compute="_compute_state_color", string="State Color", help="Color for the status badge")


class ImportWizardMixin(models.AbstractModel):
    """Mixin for import wizard models with common fields and methods."""

    _name = "flight.import.wizard.mixin"
    _description = "Import Wizard Mixin"

    # Import state
    state = fields.Selection(
        [
            ("upload", "Upload CSV"),
            ("preview", "Preview Data"),
            ("import", "Import Complete"),
        ],
        default="upload",
        string="Status",
        help="Current state of the import process",
    )
    
    # Import file
    csv_file = fields.Binary("CSV File", required=True, help="CSV file to be imported")
    filename = fields.Char("Filename", help="Name of the uploaded CSV file")
    delimiter = fields.Char("Delimiter", default=",", help="CSV delimiter character")
    
    # Statistics
    total_rows = fields.Integer("Total Rows", compute="_compute_statistics", help="Total number of rows in the CSV file")
    valid_count = fields.Integer("Valid", compute="_compute_statistics", help="Number of valid records")
    invalid_count = fields.Integer("Invalid", compute="_compute_statistics", help="Number of invalid records")
    conflict_count = fields.Integer("Conflicts", compute="_compute_statistics", help="Number of conflicting records")
    imported_count = fields.Integer("Imported", compute="_compute_statistics", help="Number of records imported")
    skipped_count = fields.Integer("Skipped", compute="_compute_statistics", help="Number of records skipped")
    
    @api.depends("line_ids", "line_ids.status", "line_ids.result")
    def _compute_statistics(self):
        """Compute import statistics based on line states."""
        for record in self:
            record.total_rows = len(record.line_ids)
            record.valid_count = len(record.line_ids.filtered(lambda l: l.status == "valid"))
            record.invalid_count = len(record.line_ids.filtered(lambda l: l.status == "invalid"))
            record.conflict_count = len(record.line_ids.filtered(lambda l: l.status == "conflict"))
            record.imported_count = len(record.line_ids.filtered(lambda l: l.result == "created" or l.result == "updated"))
            record.skipped_count = len(record.line_ids.filtered(lambda l: l.result == "skipped"))
    
    def action_reset(self):
        """Reset wizard to upload state."""
        self.ensure_one()
        self.line_ids.unlink()
        self.state = "upload"
        
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
