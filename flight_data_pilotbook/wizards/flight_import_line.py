# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import _, fields, models, api


class FlightImportLine(models.TransientModel):
    """Transient model for flight import lines."""

    _name = "flight.import.line"
    _description = "Flight Import Line"
    _rec_name = "id"
    _inherit = "flight.import.line.mixin"

    # Relation to import wizard
    wizard_id = fields.Many2one("flight.import", ondelete="cascade")
    
    # Flight data fields
    date = fields.Date("Flight Date")
    flight_number = fields.Char("Flight Number")
    departure_id = fields.Many2one("flight.aerodrome", string="Departure")
    arrival_id = fields.Many2one("flight.aerodrome", string="Arrival")
    aircraft_id = fields.Many2one("flight.aircraft", string="Aircraft")
    flight_time = fields.Float("Flight Time (hours)")
    is_simulator = fields.Boolean("Is Simulator")
    remarks = fields.Text("Remarks")
    
    # Raw data from CSV
    raw_date = fields.Char("Date (Raw)")
    raw_flight_number = fields.Char("Flight Number (Raw)")
    raw_departure = fields.Char("Departure (Raw)")
    raw_arrival = fields.Char("Arrival (Raw)")
    raw_aircraft_reg = fields.Char("Aircraft Registration (Raw)")
    raw_aircraft_make = fields.Char("Aircraft Make (Raw)")
    raw_aircraft_model = fields.Char("Aircraft Model (Raw)")
    raw_remarks = fields.Char("Remarks (Raw)")
    raw_pilot1 = fields.Char("Pilot 1 (Raw)")
    raw_pilot2 = fields.Char("Pilot 2 (Raw)")
    raw_flight_time = fields.Char("Flight Time (Raw)")
    raw_is_simulator = fields.Char("Is Simulator (Raw)")
    
    # Related fields for display
    departure_name = fields.Char(related="departure_id.name", string="Departure Name", readonly=True)
    arrival_name = fields.Char(related="arrival_id.name", string="Arrival Name", readonly=True)
    aircraft_registration = fields.Char(related="aircraft_id.registration", string="Aircraft Reg", readonly=True)
    