import logging
from odoo import fields, models
from odoo.addons.http_routing.models.ir_http import slug
from odoo.tools.translate import html_translate

_logger = logging.getLogger(__name__)

class FlightAircraft(models.Model):
    _name = "flight.aircraft"
    _inherit = [
        "flight.aircraft",
        "website.seo.metadata",
        "website.multi.mixin",
        "website.published.mixin",
        "website.cover_properties.mixin",
    ]

    def _get_default_website_description(self):
        return self.env['ir.qweb']._render("website_flight_fleet.default_website_description", raise_if_not_found=False)

    website_published = fields.Boolean(
        "Aircraft Visible on Website", 
        copy=False
    )
    website_short_description = fields.Text(
        "Website Short Description", 
        help="A short description of the aircraft that will be displayed on the website and cards",
        translate=True
    )
    website_display_name = fields.Char(
        "Website Display Name",
        help="The name that will be displayed on the website (e.g., 'Citation Bravo N550RM')",
    )
    website_aircraft_slogan = fields.Char(
        "Slogan for the aircraft", 
        translate=True,
        help="The slogan or tagline that will be displayed on the website (e.g., 'Fast and reliable')",
    )

    website_spec_header = fields.Char(
        "Website Specification Header", 
        default="Specifications",
        help="The header that will be displayed on the website for the specifications",
    )
    
    website_spec_description = fields.Text(
        "Website Specification Description", 
        translate=True,
        help="The description that will be displayed on the website for the specifications",
    )

    website_description = fields.Html(
        'Website description, static content of the aircraft', translate=html_translate,
        default=_get_default_website_description, prefetch=False,
        sanitize_overridable=True,
        sanitize_attributes=False, sanitize_form=False)

    carousel_image_ids = fields.One2many(
        'flight.aircraft.carousel.image',
        'aircraft_id',
        string='Carousel Images',
        help='Images to be displayed in the aircraft detail page carousel'
    )

    def _compute_website_url(self):
        for aircraft in self:
            aircraft.website_url = f"/aircraft/{slug(aircraft)}"