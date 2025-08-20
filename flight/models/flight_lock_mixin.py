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
        # Check if any related flight is locked before creation
        # Note: self is empty during create, so we need to check the vals_list
        for vals in vals_list:
            if 'flight_id' in vals and vals['flight_id']:
                flight = self.env['flight.flight'].browse(vals['flight_id'])
                if flight.exists() and flight.locked:
                    raise UserError(_("You cannot create records for locked flight: %s") % flight.display_name)
        return super().create(vals_list)

    def write(self, vals):
        # Allow unlocking without lock check, but validate all other changes
        # If only changing 'locked' field to False, allow it
        if vals.keys() == {'locked'} and not vals.get('locked', True):
            return super().write(vals)
        
        # For all other changes, check if records are locked
        for record in self:
            if record._is_locked():
                raise UserError(_("You cannot modify locked flights."))
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record._is_locked():
                raise UserError(_("You cannot delete records of a locked flight."))
        return super().unlink()
