from odoo import api, fields, models


class MapPathMixin(models.AbstractModel):
    """Mixin to add map data functionality to any model"""

    _name = "map.path.mixin"
    _description = "Map Path Mixin"

    map_data = fields.Json(
        string="Map Data",
        compute="_compute_map_data",
        help="JSON data containing paths and markers for map display",
    )

    @api.depends()
    def _compute_map_data(self):
        """Override this method to provide custom map data"""
        for record in self:
            record.map_data = {"paths": [], "markers": []}
