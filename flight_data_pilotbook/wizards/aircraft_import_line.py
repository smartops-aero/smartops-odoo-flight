# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import fields, models


class AircraftImportLine(models.TransientModel):
    _name = "flight.aircraft.import.line"
    _description = "Aircraft Import Line"
    _inherit = "flight.import.line.mixin"

    wizard_id = fields.Many2one(
        "flight.aircraft.import.wizard",
        string="Import Wizard",
        ondelete="cascade",
    )
    
    # CSV data fields
    registration = fields.Char(string="Registration", required=True)
    model = fields.Char(string="Model")
    operator = fields.Char(string="Operator")
    equipment_type = fields.Char(string="Equipment Type")
    engine_type = fields.Char(string="Engine Type")
    category = fields.Char(string="Category")
    
    # Related records
    aircraft_id = fields.Many2one("flight.aircraft", string="Existing Aircraft")
    model_id = fields.Many2one("flight.aircraft.model", string="Aircraft Model")
    make_id = fields.Many2one("flight.aircraft.make", string="Aircraft Make")
    class_id = fields.Many2one("flight.aircraft.class", string="Aircraft Class")
