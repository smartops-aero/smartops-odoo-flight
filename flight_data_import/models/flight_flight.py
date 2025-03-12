# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import fields, models


class FlightFlight(models.Model):
    _inherit = "flight.flight"

    # Ensure flights can be imported only once
    # if the import format provides unique transaction IDs
    unique_import_id = fields.Char(string="Import ID", readonly=True, copy=False)
    raw_data = fields.Text(string="Raw Import Data", readonly=True, copy=False)

    _sql_constraints = [
        (
            "unique_import_id",
            "unique(unique_import_id)",
            "A flight can be imported only once!"
        )
    ]
