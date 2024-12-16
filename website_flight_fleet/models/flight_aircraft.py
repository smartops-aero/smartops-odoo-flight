from odoo import api, fields, models
from odoo.addons.http_routing.models.ir_http import slug

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
    website_published = fields.Boolean("Visible on Website", copy=False)
    website_short_description = fields.Text("Website Short Description", translate=True)
    website_display_name = fields.Char(
        "Website Display Name",
        help="The name that will be displayed on the website (e.g., 'Citation Bravo N550RM')",
    )
    website_aircraft_slogan = fields.Char("Slogan for the aircraft", translate=True)

    def _compute_website_url(self):
        super()._compute_website_url()
        for aircraft in self:
            aircraft.website_url = f"/aircraft/{slug(aircraft)}"

    def _get_website_page(self):
        self.ensure_one()
        domain = [('url', '=', self.website_url)]
        return self.env['website.page'].search(domain, limit=1)

    def _get_website_view(self):
        self.ensure_one()
        view_key = f'website_flight_fleet.aircraft_page_{self.id}'
        return self.env['ir.ui.view'].search([('key', '=', view_key)], limit=1)

    def _create_website_page(self):
        self.ensure_one()
        template_view = self.env.ref('website_flight_fleet.page_aircraft_detail')
        
        # Create view using template's arch
        view_values = {
            'name': self.website_display_name or self.name,
            'type': 'qweb',
            'arch': '''
                <t t-name="website_flight_fleet.aircraft_page_%d">
                    <t t-call="website_flight_fleet.page_aircraft_detail">
                        <t t-set="aircraft" t-value="aircraft"/>
                    </t>
                </t>
            ''' % self.id,
            'key': f'website_flight_fleet.aircraft_page_{self.id}',
            'website_id': self.website_id.id,
        }
        view = self.env['ir.ui.view'].sudo().create(view_values)

        # Create website page
        page_values = {
            'url': self.website_url,
            'website_published': self.website_published,
            'view_id': view.id,
            'website_indexed': True,
            'name': self.website_display_name or self.name,
            'website_id': self.website_id.id,
            'is_published': self.website_published,
        }
        return self.env['website.page'].sudo().create(page_values)

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
                page.write({
                    'is_published': vals['website_published'],
                    'website_published': vals['website_published'],
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
