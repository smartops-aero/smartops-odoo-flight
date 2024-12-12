from odoo import fields, models

class FlightAircraft(models.Model):
    _inherit = "flight.aircraft"

    # Aircraft specifications
    seat_map_1920 = fields.Image(
        "Seat Map",
        max_width=1920,
        max_height=1920,
        help="Upload a seat map image showing the aircraft's seating configuration",
    )

    # Aircraft specifications
    passenger_capacity = fields.Integer("Passenger Capacity")
    
    range_nm = fields.Float("Range", required=True)
    range_uom_id = fields.Many2one('uom.uom', string='Range Unit of Measure', 
        domain=lambda self: [('category_id', '=', self.env.ref('flight_uom.product_uom_categ_distance').id)],
        default=lambda self: self.env.ref('flight_uom.product_uom_nm'),
        required=True)
    
    cruise_speed = fields.Float("Cruise Speed", required=True)
    cruise_speed_uom_id = fields.Many2one('uom.uom', string='Speed Unit of Measure',
        domain=lambda self: [('category_id', '=', self.env.ref('flight_uom.product_uom_categ_speed').id)],
        default=lambda self: self.env.ref('flight_uom.product_uom_kt'),
        required=True)
    
    cabin_length = fields.Float("Cabin Length")
    cabin_length_uom_id = fields.Many2one('uom.uom', string='Length Unit of Measure',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)],
        default=lambda self: self.env.ref('uom.product_uom_foot'),
        required=True)
    
    cabin_width = fields.Float("Cabin Width")
    cabin_width_uom_id = fields.Many2one('uom.uom', string='Width Unit of Measure',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)],
        default=lambda self: self.env.ref('uom.product_uom_foot'),
        required=True)
    
    cabin_height = fields.Float("Cabin Height")
    cabin_height_uom_id = fields.Many2one('uom.uom', string='Height Unit of Measure',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)],
        default=lambda self: self.env.ref('uom.product_uom_foot'),
        required=True)
    
    luggage_capacity = fields.Float("Luggage Capacity")
    luggage_capacity_uom_id = fields.Many2one('uom.uom', string='Volume Unit of Measure',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)],
        default=lambda self: self.env.ref('uom.product_uom_cubic_foot'),
        required=True)
    
    useful_load = fields.Float("Useful Load")
    useful_load_uom_id = fields.Many2one('uom.uom', string='Weight Unit of Measure',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)],
        default=lambda self: self.env.ref('uom.product_uom_lb'),
        required=True)