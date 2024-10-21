from odoo import _, api, models
from odoo.exceptions import UserError


class FlightLockMixin(models.AbstractModel):
    _name = "flight.lock.mixin"
    _description = "Flight Lock Mixin"

    def _is_locked(self):
        self.ensure_one()
        if hasattr(self, "locked") and self.locked:
            return True
        elif hasattr(self, "flight_id") and self.flight_id.locked:
            return True
        return False

    @api.model_create_multi
    def create(self, vals_list):
        for record in self:
            if record._is_locked():
                raise UserError(_("You cannot create records for a locked flight."))
        return super().create(vals_list)

    def write(self, vals):
        if len(vals) > 1 or "locked" not in vals:
            for record in self:
                if record._is_locked():
                    raise UserError(_("You cannot modify locked flights."))
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record._is_locked():
                raise UserError(_("You cannot delete records of a locked flight."))
        return super().unlink()
