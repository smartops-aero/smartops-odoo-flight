from odoo import fields, models
from odoo.addons.http_routing.models.ir_http import slug


class FlightAircraftAmenity(models.Model):
    _name = "flight.aircraft.amenity"
    _description = "Aircraft Amenity"
    _order = "sequence, name"

    name = fields.Char("Name", required=True, translate=True)
    sequence = fields.Integer("Sequence", default=10)


class FlightAircraft(models.Model):
    _name = "flight.aircraft"
    _inherit = [
        "flight.aircraft",
        "website.seo.metadata",
        "website.multi.mixin",
        "website.published.mixin",
        "website.cover_properties.mixin",
    ]

    # Existing fields
    website_published = fields.Boolean("Visible on Website", copy=False)
    website_short_description = fields.Text("Website Short Description", translate=True)
    website_display_name = fields.Char(
        "Website Display Name",
        help="The name that will be displayed on the website (e.g., 'Citation Bravo N550RM')",
    )
    website_aircraft_slogan = fields.Char("Slogan for the aircraft", translate=True)

    # Aircraft specifications
    passenger_capacity = fields.Integer("Passenger Capacity")
    range_nm = fields.Integer("Range (Nautical Miles)")
    cruise_speed = fields.Integer("Cruise Speed (Knots)")
    cabin_length = fields.Float("Cabin Length (ft)")
    cabin_width = fields.Float("Cabin Width (ft)")
    cabin_height = fields.Float("Cabin Height (ft)")
    luggage_capacity = fields.Integer("Luggage Capacity (cu ft)")
    useful_load = fields.Integer(
        "Useful Load (lb)", help="Maximum useful load in pounds"
    )

    # Amenities
    amenity_ids = fields.Many2many("flight.aircraft.amenity", string="Amenities")

    # Seat map image
    seat_map_1920 = fields.Image(
        "Seat Map",
        max_width=1920,
        max_height=1920,
        help="Upload a seat map image showing the aircraft's seating configuration",
    )

    # Additional specifications that might be needed
    is_available_for_lease = fields.Boolean("Available for Lease")
    lease_terms = fields.Text("Lease Terms")
    regional_operations = fields.Text("Regional Operations")

    def _compute_website_url(self):
        super()._compute_website_url()
        for aircraft in self:
            aircraft.website_url = f"/aircraft/{slug(aircraft)}"

    def _get_page_view_values(self, add_menu=False):
        values = super()._get_page_view_values(add_menu=add_menu)
        values.update(
            {
                "passenger_capacity": self.passenger_capacity,
                "range_nm": self.range_nm,
                "cruise_speed": self.cruise_speed,
                "cabin_dimensions": {
                    "length": self.cabin_length,
                    "width": self.cabin_width,
                    "height": self.cabin_height,
                },
                "luggage_capacity": self.luggage_capacity,
                "amenities": self.amenity_ids,
            }
        )
        return values
