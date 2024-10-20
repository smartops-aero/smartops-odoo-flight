# flight/flight/models/flight_lock_mixin.py

from odoo import _, api, models
from odoo.exceptions import UserError


class FlightLockMixin(models.AbstractModel):
    _name = "flight.lock.mixin"
    _description = "Flight Lock Mixin"

    def _check_flight_locked(self):
        if hasattr(self, "locked") and self.locked:
            return True
        elif hasattr(self, "flight_id") and self.flight_id.locked:
            return True
        return False

    @api.model
    def create(self, vals):
        if self._check_flight_locked():
            raise UserError(_("You cannot create records for a locked flight."))
        return super().create(vals)

    def write(self, vals):
        for record in self:
            if record._check_flight_locked():
                raise UserError(
                    _("You cannot modify records or fields of a locked flight.")
                )
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record._check_flight_locked():
                raise UserError(_("You cannot delete records of a locked flight."))
        return super().unlink()
