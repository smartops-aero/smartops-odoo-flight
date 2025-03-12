from odoo import api

from odoo import fields, models


class FlightPilotTimeCode(models.Model):
    _name = "flight.pilot.time.code"
    _description = "Pilot Time Code"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("unique_name", "unique(name)", "The time code name must be unique!"),
    ]

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.code:
                name = f"{record.code} - {name}"
            result.append((record.id, name))
        return result


class FlightPilotTime(models.Model):
    _name = "flight.pilot.time"
    _description = "Pilot Time"
    _order = "flight_id desc, partner_id, code_id"
    _inherit = ["flight.lock.mixin"]

    flight_id = fields.Many2one(
        "flight.flight", string="Flight", required=True, index=True, ondelete="cascade"
    )
    partner_id = fields.Many2one(
        "res.partner", string="Pilot", required=True, index=True, ondelete="restrict"
    )
    aircraft_id = fields.Many2one(
        "flight.aircraft",
        string="Aircraft",
        related="flight_id.aircraft_id",
        store=True,
        readonly=True,
    )
    code_id = fields.Many2one(
        "flight.pilot.time.code",
        string="Time Code",
        required=True,
        index=True,
        ondelete="restrict",
    )
    duration = fields.Float(string="Duration (hours)", default=0.0)
    date = fields.Date(related="flight_id.date", store=True, readonly=True)

    _sql_constraints = [
        (
            "unique_pilot_flight_code",
            "UNIQUE(flight_id, partner_id, code_id)",
            "A pilot can only have one time entry per flight and time code.",
        ),
    ]

    @api.model
    def create_from_flight_phases(self, flight, pilot, code, phase_name, time_kind="A"):
        """Create a pilot time entry based on a flight phase"""
        PhaseModel = self.env["flight.phase.duration"]
        phases = PhaseModel.search(
            [
                ("flight_id", "=", flight.id),
                ("phase_id.name", "=", phase_name),
                ("time_kind", "=", time_kind),
            ]
        )

        if not phases:
            return False

        # Get or create the time entry
        time_entry = self.search(
            [
                ("flight_id", "=", flight.id),
                ("partner_id", "=", pilot.id),
                ("code_id", "=", code.id),
            ]
        )

        if time_entry:
            time_entry.write({"duration": phases[0].duration})
        else:
            time_entry = self.create(
                {
                    "flight_id": flight.id,
                    "partner_id": pilot.id,
                    "code_id": code.id,
                    "duration": phases[0].duration,
                }
            )

        return time_entry
