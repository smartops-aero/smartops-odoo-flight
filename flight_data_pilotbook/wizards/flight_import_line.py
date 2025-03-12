# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import _, fields, models, api


class FlightImportLine(models.TransientModel):
    """Flight import line model."""

    _name = "flight.import.line"
    _description = "Flight Import Line"

    wizard_id = fields.Many2one("flight.import", string="Wizard", required=True, ondelete="cascade")
    
    # Raw data
    raw_date = fields.Char("Raw Date")
    raw_flight_number = fields.Char("Raw Flight Number")
    raw_departure = fields.Char("Raw Departure")
    raw_arrival = fields.Char("Raw Arrival")
    raw_aircraft_reg = fields.Char("Raw Aircraft Registration")
    raw_aircraft_make = fields.Char("Raw Aircraft Make")
    raw_aircraft_model = fields.Char("Raw Aircraft Model")
    raw_remarks = fields.Char("Raw Remarks")
    raw_pilot1 = fields.Char("Raw Pilot 1")
    raw_pilot2 = fields.Char("Raw Pilot 2")
    raw_flight_time = fields.Char("Raw Flight Time")
    raw_is_simulator = fields.Char("Raw Is Simulator")
    
    # Raw pilot time data
    raw_pic_time = fields.Char("Raw PIC Time")
    raw_sic_time = fields.Char("Raw SIC Time")
    raw_dual_time = fields.Char("Raw Dual Time")
    raw_instructor_time = fields.Char("Raw Instructor Time")
    raw_night_time = fields.Char("Raw Night Time")
    raw_ifr_time = fields.Char("Raw IFR Time")
    raw_capacity = fields.Char("Raw Capacity")
    
    # Processed data
    date = fields.Date("Date")
    flight_number = fields.Char("Flight Number")
    departure = fields.Char("Departure")
    arrival = fields.Char("Arrival")
    aircraft_id = fields.Many2one("flight.aircraft", string="Aircraft")
    remarks = fields.Text("Remarks")
    flight_time = fields.Float("Flight Time")
    is_simulator = fields.Boolean("Is Simulator")
    
    # Pilot time data
    pic_time = fields.Float("PIC Time")
    sic_time = fields.Float("SIC Time")
    dual_time = fields.Float("Dual Time")
    instructor_time = fields.Float("Instructor Time")
    night_time = fields.Float("Night Time")
    ifr_time = fields.Float("IFR Time")
    capacity = fields.Char("Capacity")
    
    # Pilot 1 data
    pilot1_id = fields.Char("Pilot 1 ID")
    pilot1_name = fields.Char("Pilot 1 Name")
    pilot1_phone = fields.Char("Pilot 1 Phone")
    pilot1_email = fields.Char("Pilot 1 Email")
    
    # Pilot 2 data
    pilot2_id = fields.Char("Pilot 2 ID")
    pilot2_name = fields.Char("Pilot 2 Name")
    pilot2_phone = fields.Char("Pilot 2 Phone")
    pilot2_email = fields.Char("Pilot 2 Email")
    
    # Pilot 3 data
    pilot3_id = fields.Char("Pilot 3 ID")
    pilot3_name = fields.Char("Pilot 3 Name")
    pilot3_phone = fields.Char("Pilot 3 Phone")
    pilot3_email = fields.Char("Pilot 3 Email")
    
    # Pilot 4 data
    pilot4_id = fields.Char("Pilot 4 ID")
    pilot4_name = fields.Char("Pilot 4 Name")
    pilot4_phone = fields.Char("Pilot 4 Phone")
    pilot4_email = fields.Char("Pilot 4 Email")
    
    # Status
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("valid", "Valid"),
            ("invalid", "Invalid"),
            ("imported", "Imported"),
        ],
        string="Status",
        default="draft",
    )
    error = fields.Text("Error")
    
    # Flight
    flight_id = fields.Many2one("flight.flight", string="Flight")