# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import fields, models


class AircraftImportLine(models.TransientModel):
    _name = "flight.aircraft.import.line"
    _description = "Aircraft Import Line"

    wizard_id = fields.Many2one(
        "flight.aircraft.import.wizard",
        string="Import Wizard",
        required=True,
        ondelete="cascade",
    )
    
    # CSV data fields
    registration = fields.Char(string="Registration", required=True)
    model_name = fields.Char(string="Model")
    operator = fields.Char(string="Operator")
    equipment_type = fields.Char(string="Equipment Type")
    engine_type = fields.Char(string="Engine Type")
    category = fields.Char(string="Category")
    
    # Processing fields
    to_import = fields.Boolean(string="Import", default=True)
    status = fields.Selection(
        [
            ("valid", "Valid"),
            ("invalid", "Invalid"),
            ("conflict", "Conflict"),
        ],
        string="Status",
        default="valid",
    )
    message = fields.Text(string="Message")
    result = fields.Selection(
        [
            ("created", "Created"),
            ("updated", "Updated"),
            ("skipped", "Skipped"),
        ],
        string="Result",
    )
    
    # Related records
    aircraft_id = fields.Many2one("flight.aircraft", string="Existing Aircraft")
    model_id = fields.Many2one("flight.aircraft.model", string="Aircraft Model")
    make_id = fields.Many2one("flight.aircraft.make", string="Aircraft Make")
    class_id = fields.Many2one("flight.aircraft.class", string="Aircraft Class")
