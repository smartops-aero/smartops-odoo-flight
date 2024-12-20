from odoo import fields, models, api, _

class FlightAircraftImage(models.Model):
    _name = 'flight.aircraft.image'
    _description = 'Aircraft Image'
    _order = 'sequence, id'

    name = fields.Char('Name')
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', default=10)
    image = fields.Binary('Image', required=True, attachment=True)
    aircraft_id = fields.Many2one(
        'flight.aircraft',
        string='Aircraft',
        required=True,
        ondelete='cascade'
    )

    category_id = fields.Many2one(
        'flight.aircraft.image.category',
        string='Category',
        required=True,
        ondelete='restrict'
    )

    @api.model_create_multi
    def create(self, vals_list):
        # Automatically generate names for images if not provided
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = _("Image %s") % fields.Date.today()
        return super().create(vals_list)