# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FlightCrewRole(models.Model):
    _name = "flight.crew.role"
    _description = "Crew Member Role"

    name = fields.Char(required=True)
    description = fields.Char()


class FlightCrew(models.Model):
    _name = "flight.crew"
    _description = "Crew Member"
    _inherit = ["flight.lock.mixin"]

    partner_id = fields.Many2one("res.partner", string="Contact", required=True)
    role_id = fields.Many2one("flight.crew.role")
    flight_id = fields.Many2one(
        "flight.flight", string="Flight", required=True, ondelete="cascade"
    )

    @api.depends("partner_id", "role_id")
    def _compute_display_name(self):
        """Compute display name to show partner name and role"""
        for record in self:
            name_parts = []
            if record.partner_id:
                name_parts.append(record.partner_id.name)
            if record.role_id:
                name_parts.append(f"({record.role_id.name})")
            
            record.display_name = " ".join(name_parts) if name_parts else f"Crew Member #{record.id}"

    @api.constrains("partner_id")
    def _check_crew_identification(self):
        for record in self:
            if not record.partner_id:
                raise ValidationError(
                    _("A contact must be specified for crew assignment.")
                )
