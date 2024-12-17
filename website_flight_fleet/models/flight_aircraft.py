from odoo import api, fields, models
from odoo.addons.http_routing.models.ir_http import slug
import logging

class FlightAircraft(models.Model):
    _name = "flight.aircraft"
    _inherit = [
        "flight.aircraft",
        "website.seo.metadata",
        "website.multi.mixin",
        "website.published.mixin",
        "website.cover_properties.mixin",
    ]

    # Website Fields
    website_published = fields.Boolean("Aircraft Visible on Website", copy=False)
    website_short_description = fields.Text("Website Short Description", 
    help="A short description of the aircraft that will be displayed on the website",
    translate=True)
    website_display_name = fields.Char(
        "Website Display Name",
        help="The name that will be displayed on the website (e.g., 'Citation Bravo N550RM')",
    )
    website_aircraft_slogan = fields.Char("Slogan for the aircraft", translate=True)

    def _get_view_key(self):
        """Generate the unique view key for this aircraft"""
        self.ensure_one()
        return f'website_flight_fleet.aircraft_page_{self.id}'

    def _get_page_name(self):
        """Get display name for website page"""
        self.ensure_one()
        return self.website_display_name or self.name

    def _compute_website_url(self):
        for aircraft in self:
            aircraft.website_url = f"/aircraft/{slug(aircraft)}"

    def _get_website_page(self):
        self.ensure_one()
        domain = [('url', '=', self.website_url)]
        return self.env['website.page'].sudo().search(domain, limit=1)

    def _get_website_view(self):
        self.ensure_one()
        view_key = self._get_view_key()
        return self.env['ir.ui.view'].sudo().search([('key', '=', view_key)], limit=1)

    def _create_website_page(self):
        self.ensure_one()
        View = self.env['ir.ui.view'].sudo()
        Page = self.env['website.page'].sudo()
        view = None
        try:
            template_view = self.env.ref('website_flight_fleet.page_aircraft_detail')
            view_key = self._get_view_key()
            page_name = self._get_page_name()
        
            if not template_view:
                raise ValueError("Template view 'website_flight_fleet.page_aircraft_detail' not found")
            
            # Get the template's arch and replace the template id and name
            arch = template_view.arch.replace(
                'id="page_aircraft_detail"', 
                f'id="{view_key}"'
            ).replace(
                'name="Aircraft Detail"',
                f'name="{page_name}"'
            )
            
            view_values = {
                'name': page_name,
                'type': 'qweb',
                'mode': 'primary',
                'arch': arch,
                'key': view_key,
                'website_id': self.website_id.id if self.website_id else None,
                'active': True,
            }

            view = View.with_context(website_id=self.website_id.id).sudo().create(view_values)
            published_state = self.website_published
            page_values = {
                'url': self.website_url,
                'website_published': published_state,
                'view_id': view.id,
                'website_indexed': True,
                'name': page_name,
                'website_id': self.website_id.id,
                'is_published': published_state,
                'track': True,
            }
            
            return self.env['website.page'].sudo().create(page_values)
            
        except Exception as e:
            if view:
                view.sudo().unlink()
            raise e

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if not record._get_website_page():
                record._create_website_page()
        return records

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            page = record._get_website_page()
            if not page:
                record._create_website_page()
            elif 'website_published' in vals:
                published_state = vals['website_published']
                page.write({
                    'is_published': published_state,
                    'website_published': published_state,
                })
        return res

    def unlink(self):
        # Get pages and views before deletion
        pages = self.mapped(lambda r: r._get_website_page())
        views = self.mapped(lambda r: r._get_website_view())
        
        res = super().unlink()
        
        # Clean up pages and views
        if pages:
            pages.unlink()
        if views:
            views.unlink()
        return res
