from odoo import fields, models
from odoo.addons.http_routing.models.ir_http import slug
from odoo.tools.translate import html_translate


class FlightAircraft(models.Model):
    _name = "flight.aircraft"
    _inherit = [
        "flight.aircraft",
        "website.seo.metadata",
        "website.multi.mixin",
        "website.published.mixin",
        "website.cover_properties.mixin",
    ]

    def _get_default_hero_content(self):
        return self.env['ir.qweb']._render("website_flight_fleet.aircraft_hero_content", raise_if_not_found=False)

    def _get_default_main_carousel_content(self):
        return self.env['ir.qweb']._render("website_flight_fleet.aircraft_main_carousel_content", raise_if_not_found=False)

    def _get_default_spec_header_content(self):
        return self.env['ir.qweb']._render("website_flight_fleet.aircraft_spec_header_content", raise_if_not_found=False)

    def _get_default_interior_gallery_header_content(self):
        return self.env['ir.qweb']._render("website_flight_fleet.aircraft_interior_gallery_header_content", raise_if_not_found=False)

    def _get_default_interior_gallery_carousel_content(self):
        return self.env['ir.qweb']._render("website_flight_fleet.aircraft_interior_gallery_carousel_content", raise_if_not_found=False)

    def _get_default_benefits_content(self):
        return self.env['ir.qweb']._render("website_flight_fleet.aircraft_benefits_content", raise_if_not_found=False)

    def _get_default_faq_header_content(self):
        return self.env['ir.qweb']._render("website_flight_fleet.aircraft_faq_header_content", raise_if_not_found=False)

    def _get_default_faq_content(self):
        return self.env['ir.qweb']._render("website_flight_fleet.aircraft_faq_content", raise_if_not_found=False)

    def _get_default_cta_content(self):
        return self.env['ir.qweb']._render("website_flight_fleet.aircraft_cta_content", raise_if_not_found=False)

    # Existing fields
    website_published = fields.Boolean("Visible on Website", copy=False)
    website_short_description = fields.Text("Website Short Description", translate=True)
    website_display_name = fields.Char(
        "Website Display Name",
        help="The name that will be displayed on the website (e.g., 'Citation Bravo N550RM')",
    )
    website_aircraft_slogan = fields.Char("Slogan for the aircraft", translate=True)

    # Editable Content Fields
    hero_content = fields.Html(
        "Hero Content",
        translate=html_translate,
        sanitize=False,
        default=_get_default_hero_content,
    )

    spec_header_content = fields.Html(
        "Specifications Header",
        translate=html_translate,
        sanitize=False,
        default=_get_default_spec_header_content,
    )

    interior_gallery_header_content = fields.Html(
        "Interior Gallery Header",
        translate=html_translate,
        sanitize=False,
        default=_get_default_interior_gallery_header_content,
    )

    benefits_content = fields.Html(
        "Benefits Section",
        translate=html_translate,
        sanitize=False,
        default=_get_default_benefits_content,
    )
    faq_header_content = fields.Html(
        "FAQ Header",
        translate=html_translate,
        sanitize=False,
        default=_get_default_faq_header_content,
    )

    faq_content = fields.Html(
        "FAQ Section",
        translate=html_translate,
        sanitize=False,
        default=_get_default_faq_content,
    )
    main_carousel_content = fields.Html(
        "Main Carousel Content",
        translate=html_translate,
        sanitize=False,
        default=_get_default_main_carousel_content,
    )
    interior_gallery_carousel_content = fields.Html(
        "Gallery Carousel Content",
        translate=html_translate,
        sanitize=False,
        default=_get_default_interior_gallery_carousel_content,
    )
    cta_content = fields.Html(
        "Call to Action Section",
        translate=html_translate,
        sanitize=False,
        default=_get_default_cta_content,
    )

    def _compute_website_url(self):
        super()._compute_website_url()
        for aircraft in self:
            aircraft.website_url = f"/aircraft/{slug(aircraft)}"

    def _get_page_view_values(self, add_menu=False):
        values = super()._get_page_view_values(add_menu=add_menu)
        values.update(
            {
                "passenger_capacity": self.passenger_capacity,
                "range": self.range,
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
