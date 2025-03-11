from odoo import api, fields, models, _


class PilotImportLine(models.TransientModel):
    _name = 'flight.pilot.import.line'
    _description = 'Pilot Import Line'
    
    import_id = fields.Many2one('flight.pilot.import.wizard', string='Import', required=True, ondelete='cascade')
    
    # Data fields
    name = fields.Char(string='Name', required=True)
    employee_id = fields.Char(string='Employee ID')
    company = fields.Char(string='Company')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    notes = fields.Text(string='Notes')
    
    # Status fields
    status = fields.Selection([
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('conflict', 'Conflict')
    ], string='Status', default='valid')
    
    message = fields.Char(string='Message')
    
    # Import control
    to_import = fields.Boolean(string='Import', default=True)
    
    # Result
    result = fields.Selection([
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('skipped', 'Skipped')
    ], string='Result')
