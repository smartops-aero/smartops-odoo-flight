# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import api, fields, models


class FlightNumber(models.Model):
    _name = "flight.number"
    _description = "Flight Number"

    prefix_id = fields.Many2one("flight.prefix")
    number = fields.Char()

    @api.depends('prefix_id.name', 'number')
    def _compute_display_name(self):
        for record in self:
            prefix_name = record.prefix_id.name if record.prefix_id else ''
            number = record.number if record.number else ''
            record.display_name = f"{prefix_name}{number}"

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        if operator == "ilike" and not (name or "").strip():
            domain = []
        elif operator in ("ilike", "like"):
            domain = [
                "|",
                ("prefix_id.name", operator, name),
                ("number", operator, name),
            ]
        else:
            domain = [
                "|",
                ("prefix_id.name", operator, name),
                ("number", operator, name),
            ]

        # In Odoo 18.0, _search doesn't accept access_rights_uid parameter
        # The name_get_uid parameter is maintained for API compatibility but not used
        return self._search(domain + args, limit=limit)


class FlightPrefix(models.Model):
    _name = "flight.prefix"
    _description = "Flight Number Prefix"

    name = fields.Char("Prefix")
    description = fields.Char()
