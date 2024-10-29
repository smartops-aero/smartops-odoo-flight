from odoo import models


class FlightFlight(models.Model):
    _name = "flight.flight"
    _inherit = ["flight.flight", "portal.mixin"]

    def _get_share_url(self, redirect=False, signup_partner=False, share_token=None):
        """Override from portal.mixin to handle the flight specific URL."""
        self.ensure_one()
        if not share_token:
            share_token = self.access_token or self._portal_ensure_token()
        return f"/my/flight/{self.id}?access_token={share_token}"

    def _compute_access_url(self):
        """Override from portal.mixin to handle the flight specific URL."""
        super()._compute_access_url()
        for flight in self:
            flight.access_url = f"/my/flight/{flight.id}"

    def action_share(self):
        """Generate a share popup action."""
        self.ensure_one()
        # Get base URL for the current database
        base_url = self.get_base_url()

        # Ensure we have a valid share token
        share_token = self.access_token or self._portal_ensure_token()

        # Generate the full shareable URL
        share_url = f"{base_url}/my/flight/{self.id}?access_token={share_token}"

        # Return the share wizard action
        return {
            "type": "ir.actions.act_window",
            "name": "Share Flight",
            "res_model": "portal.share",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
                "default_share_link": share_url,
            },
        }
