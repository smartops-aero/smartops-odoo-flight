from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FlightRelatedMixin(models.AbstractModel):
    _name = "flight.related.mixin"
    _description = "Flight Related Mixin"

    flight_id = fields.Many2one(
        "flight.flight", string="Flight", required=True, ondelete="cascade"
    )

    @api.model
    def create(self, vals):
        if "flight_id" in vals:
            flight = self.env["flight.flight"].browse(vals["flight_id"])
            if flight.locked:
                raise UserError(_("You cannot create records for a locked flight."))
        return super().create(vals)

    def write(self, vals):
        for record in self:
            if record.flight_id.locked:
                raise UserError(_("You cannot modify records of a locked flight."))
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.flight_id.locked:
                raise UserError(_("You cannot delete records of a locked flight."))
        return super().unlink()
