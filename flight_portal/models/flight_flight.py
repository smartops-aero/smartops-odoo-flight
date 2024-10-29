from odoo import models


class FlightFlight(models.Model):
    _name = "flight.flight"
    _inherit = ["flight.flight", "portal.mixin"]

    def _get_share_url(self, redirect=False, signup_partner=False, share_token=None):
        """Override from portal.mixin to handle the flight specific URL."""
        self.ensure_one()
        return f"/my/flight/{self.id}"

    def _compute_access_url(self):
        """Override from portal.mixin to handle the flight specific URL."""
        super()._compute_access_url()
        for flight in self:
            flight.access_url = f"/my/flight/{flight.id}"
