import logging
from odoo import api, fields, models
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

    def _create_description_template(self):
        """Create a new ir.ui.view record for this aircraft's description"""
        self.ensure_one()
        default_template = self.env.ref('website_flight_fleet.default_website_description')
        
        View = self.env['ir.ui.view']
        key = f'website_flight_fleet.aircraft_description_{self.id}'
        
        # Create the view
        new_view = View.create({
            'name': f'Aircraft Description: {self.registration or "New"}',
            'type': 'qweb',
            'mode': 'primary',
            'arch_db': default_template.arch,
            'key': key,
            'website_id': self.env['website'].get_current_website().id,
            'priority': 16,
        })
        
        # Create XML ID for the view
        self.env['ir.model.data'].create({
            'module': 'website_flight_fleet',
            'name': f'aircraft_description_{self.id}',
            'model': 'ir.ui.view',
            'res_id': new_view.id,
            'noupdate': True,
        })
        
        return new_view

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            # Create a new template for each new aircraft
            template = record._create_description_template()
            record.website_description_view_id = template.id
        return records

    def write(self, values):
        # If registration changes, update the template name
        if 'registration' in values:
            for record in self:
                if record.website_description_view_id:
                    record.website_description_view_id.name = f'Aircraft Description: {values["registration"]}'
        return super().write(values)

    def unlink(self):
        # Clean up custom templates when aircraft is deleted
        templates = self.mapped('website_description_view_id')
        xml_ids = self.env['ir.model.data'].search([
            ('model', '=', 'ir.ui.view'),
            ('res_id', 'in', templates.ids)
        ])
        res = super().unlink()
        if xml_ids:
            xml_ids.unlink()
        if templates:
            templates.unlink()
        return res

    website_published = fields.Boolean("Aircraft Visible on Website", copy=False)
    website_short_description = fields.Text(
        "Website Short Description", 
        help="A short description of the aircraft that will be displayed on the website",
        translate=True
    )
    website_display_name = fields.Char(
        "Website Display Name",
        help="The name that will be displayed on the website (e.g., 'Citation Bravo N550RM')",
    )
    website_aircraft_slogan = fields.Char("Slogan for the aircraft", translate=True)
    
    website_description_view_id = fields.Many2one(
        'ir.ui.view',
        string='Website Description Template',
        ondelete='cascade',
        copy=False,
    )

    def _compute_website_url(self):
        for aircraft in self:
            aircraft.website_url = f"/aircraft/{slug(aircraft)}"