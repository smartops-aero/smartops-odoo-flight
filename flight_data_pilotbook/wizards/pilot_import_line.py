# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import fields, models


class PilotImportLine(models.TransientModel):
    _name = "flight.pilot.import.line"
    _description = "Pilot Import Line"
    _inherit = "flight.import.line.mixin"

    wizard_id = fields.Many2one(
        "flight.pilot.import.wizard",
        string="Import Wizard",
        required=True,        
        ondelete="cascade",
    )
    
    # CSV data fields
    name = fields.Char(string="Name", required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    license_number = fields.Char(string="License Number")
    license_type = fields.Char(string="License Type")
    license_country = fields.Char(string="License Country")
    employee_id = fields.Char(string="Employee ID")
    company = fields.Char(string="Company")
    notes = fields.Text(string="Notes")
    
    # Related records
    pilot_id = fields.Many2one("flight.pilot", string="Existing Pilot")
