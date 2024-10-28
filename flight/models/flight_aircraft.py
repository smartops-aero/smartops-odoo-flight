# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import fields, models


class FlightAircraftClass(models.Model):
    _name = "flight.aircraft.class"
    _description = "Aircraft Category and Class"

    aircraft_category = fields.Selection(
        [
            ("airplane", "Airplane"),
            ("rotorcraft", "Rotorcraft"),
            ("glider", "Glider"),
            ("lighter_than_air", "Lighter than Air"),
            ("powered_lift", "Powered Lift"),
            ("powered_parachute", "Powered Parachute"),
            ("weight_shift_control", "Weight Shift Control"),
        ],
        string="Aircraft Category",
        help="Select the category of the aircraft",
    )

    name = fields.Char("Aircraft class")


class FlightAircraftMake(models.Model):
    _name = "flight.aircraft.make"
    _description = "Aircraft Make"

    name = fields.Char()


class FlightAircraftModelTag(models.Model):
    _name = "flight.aircraft.model.tag"
    _description = "Aircraft Model Tag"

    name = fields.Char()


class FlightAircraftModel(models.Model):
    _name = "flight.aircraft.model"
    _description = "Aircraft Model"

    name = fields.Char()
    make_id = fields.Many2one("flight.aircraft.make")
    class_id = fields.Many2one("flight.aircraft.class")

    engine_type = fields.Selection(
        [
            ("diesel", "Diesel"),
            ("electric", "Electric"),
            ("non_powered", "Non-Powered"),
            ("piston", "Piston"),
            ("radial", "Radial"),
            ("turbofan", "Turbofan"),
            ("turbojet", "Turbojet"),
            ("turboprop", "Turboprop"),
            ("turboshaft", "Turboshaft"),
        ],
        string="Engine Type",
        help="Select the engine type of the aircraft",
    )

    gear_type = fields.Selection(
        [
            ("amphibian", "Amphibian (AM)"),
            ("fixed_tailwheel", "Fixed Tailwheel (FC)"),
            ("fixed_tricycle", "Fixed Tricycle (FT)"),
            ("floats", "Floats (FL)"),
            ("retractable_tailwheel", "Retractable Tailwheel (RC)"),
            ("retractable_tricycle", "Retractable Tricycle (RT)"),
            ("skids", "Skids"),
            ("skis", "Skis"),
        ],
        string="Gear Type",
        help="Select the gear type of the aircraft",
    )

    code = fields.Char("ICAO type code")

    tag_ids = fields.Many2many("flight.aircraft.model.tag")


class FlightAircraft(models.Model):
    _name = "flight.aircraft"
    _description = "Aircraft"
    _inherit = ["mail.thread", "mail.activity.mixin", "avatar.mixin"]
    _rec_name = "registration"
    _avatar_name_field = "registration"

    registration = fields.Char("Aircraft registration", tracking=True)
    model_id = fields.Many2one("flight.aircraft.model", tracking=True)
    operator_id = fields.Many2one(
        "res.partner",
        string="Operator",
        tracking=True,
        help="The company or individual operating this aircraft",
    )
    sn = fields.Char("Aircraft serial number", tracking=True)
    dom = fields.Date("Date/year of manufacture", tracking=True)
    equipment_type = fields.Selection(
        [
            ("aircraft", "Aircraft"),
            ("ffs", "Full Flight Simulator (FFS)"),
            ("ftd", "Flight Training Device (FTD)"),
            ("batd", "Basic Aircraft Training Device (BATD)"),
            ("aatd", "Advanced Aircraft Training Device (AATD)"),
        ],
        string="Equipment Type",
        default="aircraft",
        tracking=True,
    )
    mtow = fields.Float(
        "Maximum take-off weight",
        tracking=True,
        help="Maximum take-off weight of the aircraft",
    )
    weight_uom_id = fields.Many2one(
        "uom.uom",
        string="Weight Unit of Measure",
        domain=lambda self: [
            ("category_id", "=", self.env.ref("uom.product_uom_categ_kgm").id)
        ],
        default=lambda self: self.env.ref("uom.product_uom_lb"),
        required=True,
        tracking=True,
    )

    _sql_constraints = [
        (
            "registration_unique",
            "unique(registration)",
            "Aircraft with this registration number already exists!",
        )
    ]
