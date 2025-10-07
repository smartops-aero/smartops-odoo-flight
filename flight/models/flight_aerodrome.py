# Copyright 2024 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

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

    city = fields.Char(index=True)
    municipality = fields.Char()

    country_id = fields.Many2one(
        "res.country", string="Country", ondelete="restrict", index=True
    )
    country_code = fields.Char(related="country_id.code", string="Country Code")

    elevation = fields.Integer("Aerodrome elevation in feet")

    tz = fields.Selection(_tz_get, string="Timezone")

    latitude = fields.Float(string="Geo Latitude", digits=(10, 7))
    longitude = fields.Float(string="Geo Longitude", digits=(10, 7))

    # Runways
    runway_ids = fields.One2many(
        "flight.aerodrome.runway",
        "aerodrome_id",
        string="Runways",
        help="Available runways at this aerodrome",
    )

    _sql_constraints = [
        ("icao_unique", "unique(icao)", "Aerodrome with this ICAO already exists!"),
    ]

    @api.constrains("latitude", "longitude")
    def _check_coordinates(self):
        """Validate latitude and longitude are within valid ranges"""
        for record in self:
            if record.latitude and not (-90 <= record.latitude <= 90):
                raise ValidationError(
                    _("Latitude must be between -90 and 90 degrees. Got: %s")
                    % record.latitude
                )
            if record.longitude and not (-180 <= record.longitude <= 180):
                raise ValidationError(
                    _("Longitude must be between -180 and 180 degrees. Got: %s")
                    % record.longitude
                )

    @api.depends("icao", "iata", "name")
    def _compute_display_name(self):
        for record in self:
            # Build display name with safe field access
            parts = []

            # Add ICAO/IATA identifier part
            if record.iata and record.icao:
                parts.append(f"{record.icao}({record.iata})")
            elif record.icao:
                parts.append(record.icao)
            elif record.iata:
                parts.append(record.iata)

            # Add name if available
            if record.name:
                parts.append(record.name)

            # Join non-empty parts
            record.display_name = (
                " - ".join(parts) if parts else f"Aerodrome #{record.id}"
            )
