# flight_import/wizards/import_wizard.py
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FlightImportWizard(models.TransientModel):
    _name = "flight.import.wizard"
    _description = "Flight Data Import Wizard"

    config_id = fields.Many2one(
        "flight.import.config", string="Import Configuration", required=True,
        help="Select the import configuration to use for this import"
    )
    file = fields.Binary(string="Import File", required=True)
    file_name = fields.Char(string="File Name")
    
    # Results
    state = fields.Selection([
        ("draft", "Draft"),
        ("done", "Completed"),
    ], default="draft")
    
    import_log = fields.Text(string="Import Log", readonly=True)
    
    # Statistics
    processed_count = fields.Integer(string="Processed", readonly=True)
    error_count = fields.Integer(string="Errors", readonly=True)
    
    flight_count = fields.Integer(string="Flights Created/Updated", readonly=True)
    aircraft_count = fields.Integer(string="Aircraft Created/Updated", readonly=True)
    time_count = fields.Integer(string="Pilot Times Created", readonly=True)
    event_count = fields.Integer(string="Pilot Events Created", readonly=True)
    
    error_details = fields.Text(string="Error Details", readonly=True)

    @api.model
    def default_get(self, fields):
        """Set default configuration if only one exists"""
        res = super().default_get(fields)
        
        configs = self.env["flight.import.config"].search([])
        if len(configs) == 1:
            res["config_id"] = configs.id
            
        return res

    def action_import(self):
        """Import the file using the selected configuration"""
        self.ensure_one()
        
        if not self.file:
            raise UserError(_("Please select a file to import"))
            
        if not self.config_id:
            raise UserError(_("Please select an import configuration"))
            
        try:
            # Perform the import
            importer = self.env["flight.data.importer"]
            stats = importer.import_csv_data(self.file, self.config_id.id)
            
            # Update statistics
            self.write({
                "state": "done",
                "processed_count": stats.get("processed", 0),
                "error_count": len(stats.get("errors", [])),
                "flight_count": stats.get("created", {}).get("flight", 0) + stats.get("updated", {}).get("flight", 0),
                "aircraft_count": stats.get("created", {}).get("aircraft", 0) + stats.get("updated", {}).get("aircraft", 0),
                "time_count": 0,  # Will be calculated from database
                "event_count": 0,  # Will be calculated from database
            })
            
            # Count created pilot times and events
            if stats.get("processed", 0) > 0:
                # Count pilot times created in this import (approximate)
                self.time_count = self.env["flight.pilot.time"].search_count([
                    ("create_date", ">=", self.create_date)
                ])
                
                # Count pilot events created in this import (approximate)
                self.event_count = self.env["flight.pilot.event"].search_count([
                    ("create_date", ">=", self.create_date)
                ])
            
            # Generate import log
            log_lines = [
                _("Import completed with the following results:"),
                _("- Processed: %s rows") % stats.get("processed", 0),
                _("- Flights: %s created, %s updated") % (
                    stats.get("created", {}).get("flight", 0),
                    stats.get("updated", {}).get("flight", 0)
                ),
                _("- Aircraft: %s created, %s updated") % (
                    stats.get("created", {}).get("aircraft", 0),
                    stats.get("updated", {}).get("aircraft", 0)
                ),
                _("- Pilot Times: approximately %s created") % self.time_count,
                _("- Pilot Events: approximately %s created") % self.event_count,
                _("- Errors: %s") % len(stats.get("errors", [])),
            ]
            
            self.import_log = "\n".join(log_lines)
            
            # Generate error details
            if stats.get("errors"):
                error_lines = [_("Error Details:")]
                for error in stats.get("errors", []):
                    error_lines.append(_("Row %s: %s") % (error.get("row", "?"), error.get("error", "Unknown error")))
                self.error_details = "\n".join(error_lines)
            
            return {
                "name": _("Import Result"),
                "type": "ir.actions.act_window",
                "res_model": "flight.import.wizard",
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
            }
        
        except Exception as e:
            self.error_details = str(e)
            raise UserError(_("An error occurred during import: %s") % str(e))
