from odoo import api, fields, models


class FlightFlight(models.Model):
    _name = "flight.flight"
    _description = "Flight"
    _inherit = ["mail.thread", "mail.activity.mixin", "flight.lock.mixin"]
    _order = "date desc, id desc"

    date = fields.Date(
        "Flight Date", help="Scheduled date of flight", required=True, tracking=True
    )
    aircraft_id = fields.Many2one("flight.aircraft", required=True, tracking=True)
    departure_id = fields.Many2one("flight.aerodrome", required=True, tracking=True)
    arrival_id = fields.Many2one("flight.aerodrome", required=True, tracking=True)
    locked = fields.Boolean(default=False, tracking=True)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.date} / {record.aircraft_id.registration}: {record.departure_id.icao} - {record.arrival_id.icao}"
            result.append((record.id, name))
        return result

    def toggle_locked(self):
        for record in self:
            record.locked = not record.locked

    @api.model
    def action_lock_flights(self):
        self.write({"locked": True})

    @api.model
    def action_unlock_flights(self):
        self.write({"locked": False})
