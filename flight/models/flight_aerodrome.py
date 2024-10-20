# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import api, fields, models

from odoo.addons.base.models.res_partner import _tz_get


class FlightAerodrome(models.Model):
    _name = "flight.aerodrome"
    _description = "Aerodrome"
    _rec_name = "icao"
    _rec_names_search = ["icao", "iata"]

    _inherit = ["mail.thread"]

    name = fields.Char(index=True)

    icao = fields.Char("ICAO identifier", index=True, required=True)
    iata = fields.Char("IATA identifier", index=True)
    lid = fields.Char("FAA identifier")

    city = fields.Char()
    municipality = fields.Char()

    country_id = fields.Many2one("res.country", string="Country", ondelete="restrict")
    country_code = fields.Char(related="country_id.code", string="Country Code")

    elevation = fields.Integer("Aerodrome elevation in feet")

    tz = fields.Selection(_tz_get, string="Timezone")

    latitude = fields.Float(string="Geo Latitude", digits=(10, 7))
    longitude = fields.Float(string="Geo Longitude", digits=(10, 7))

    _sql_constraints = [
        ("icao_unique", "unique(icao)", "Aerodrome with this ICAO already exists!"),
    ]

    @api.depends("icao", "iata")
    def _compute_display_name(self):
        for record in self:
            record.display_name = " - ".join(
                filter(
                    None,
                    [
                        f"{record.icao}({record.iata})" if record.iata else record.icao,
                        record.name,
                    ],
                )
            )
