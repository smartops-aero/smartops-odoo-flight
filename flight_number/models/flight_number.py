# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import api, fields, models


class FlightNumber(models.Model):
    _name = "flight.number"
    _description = "Flight Number"

    prefix_id = fields.Many2one("flight.prefix")
    number = fields.Char()

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.prefix_id.name}{record.number}"
            result.append((record.id, name))
        return result

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

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


class FlightPrefix(models.Model):
    _name = "flight.prefix"
    _description = "Flight Number Prefix"

    name = fields.Char("Prefix")
    description = fields.Char()
