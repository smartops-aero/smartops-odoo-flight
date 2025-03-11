import base64
import csv
import io
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PilotImport(models.TransientModel):
    _name = 'flight.pilot.import.wizard'
    _description = 'Import Pilots from CSV'

    # File Upload Fields
    csv_file = fields.Binary(string='CSV File', required=True)
    file_name = fields.Char(string='File Name')
    delimiter = fields.Char(string='Delimiter', default=';', help='CSV file delimiter')
    
    # Field Mapping
    company_field = fields.Char(string='Company Field', default='Company', 
                               help='CSV header for company field')
    employee_id_field = fields.Char(string='Employee ID Field', default='Employee ID', 
                                   help='CSV header for employee ID field')
    name_field = fields.Char(string='Name Field', default='Pilot FullName', 
                            help='CSV header for name field')
    phone_field = fields.Char(string='Phone Field', default='Phone', 
                             help='CSV header for phone field')
    email_field = fields.Char(string='Email Field', default='Email', 
                             help='CSV header for email field')
    notes_field = fields.Char(string='Notes Field', default='Notes', 
                             help='CSV header for notes field')
    
    # Options
    create_companies = fields.Boolean(string='Create Companies', default=True,
                                     help='Create companies if they do not exist')
    
    # Import State
    state = fields.Selection([
        ('upload', 'Upload File'),
        ('preview', 'Preview Data'),
        ('import', 'Import Complete')
    ], default='upload', string='Import State')
    
    # Preview Data
    import_line_ids = fields.One2many('flight.pilot.import.line', 'import_id', 
                                     string='Import Lines')
    
    # Statistics
    total_rows = fields.Integer(string='Total Rows', readonly=True)
    valid_rows = fields.Integer(string='Valid Rows', readonly=True)
    invalid_rows = fields.Integer(string='Invalid Rows', readonly=True)
    conflict_rows = fields.Integer(string='Conflicts', readonly=True)
    
    @api.model
    def default_get(self, fields_list):
        """Set default values for the wizard"""
        res = super().default_get(fields_list)
        return res
    
    def action_parse_file(self):
        """Parse the uploaded CSV file and prepare preview data"""
        self.ensure_one()
        
        if not self.csv_file:
            raise UserError(_('Please upload a CSV file first.'))
            
        # Process the CSV file
        csv_data = base64.b64decode(self.csv_file)
        csv_file = io.StringIO(csv_data.decode('utf-8'))
        
        # Read the CSV file
        reader = csv.DictReader(csv_file, delimiter=self.delimiter)
        
        # Check if required headers exist
        required_headers = [self.name_field]
        for header in required_headers:
            if header not in reader.fieldnames:
                raise UserError(_('Required header "%s" not found in the CSV file.') % header)
        
        # Prepare for import
        Partner = self.env['res.partner']
        
        # Clear existing import lines
        self.import_line_ids.unlink()
        
        # Statistics
        stats = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'conflict': 0,
        }
        
        # Process each row
        for row in reader:
            stats['total'] += 1
            
            # Skip empty rows
            if not row[self.name_field] or row[self.name_field].strip() == '':
                stats['invalid'] += 1
                self._create_import_line(row, 'invalid', 'Empty name field')
                continue
                
            # Prepare partner values for validation
            name = row[self.name_field].strip()
            employee_id = row.get(self.employee_id_field, '').strip()
            company_name = row.get(self.company_field, '').strip()
            
            # Check for existing partner
            domain = [('name', '=', name)]
            if employee_id:
                domain = ['|', ('barcode', '=', employee_id)] + domain
                
            existing_partner = Partner.search(domain, limit=1)
            
            if existing_partner:
                stats['conflict'] += 1
                self._create_import_line(row, 'conflict', 'Partner already exists')
            else:
                stats['valid'] += 1
                self._create_import_line(row, 'valid', 'Ready to import')
        
        # Update statistics
        self.write({
            'total_rows': stats['total'],
            'valid_rows': stats['valid'],
            'invalid_rows': stats['invalid'],
            'conflict_rows': stats['conflict'],
            'state': 'preview'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def _create_import_line(self, row, status, message):
        """Create an import line for preview"""
        self.ensure_one()
        
        vals = {
            'import_id': self.id,
            'name': row.get(self.name_field, '').strip(),
            'employee_id': row.get(self.employee_id_field, '').strip(),
            'company': row.get(self.company_field, '').strip(),
            'phone': row.get(self.phone_field, '').strip(),
            'email': row.get(self.email_field, '').strip(),
            'notes': row.get(self.notes_field, '').strip(),
            'status': status,
            'message': message,
            'to_import': status == 'valid',
        }
        
        return self.env['flight.pilot.import.line'].create(vals)
    
    def action_import(self):
        """Import the selected lines"""
        self.ensure_one()
        
        # Get lines to import
        lines_to_import = self.import_line_ids.filtered(lambda l: l.to_import)
        
        if not lines_to_import:
            raise UserError(_('No lines selected for import.'))
        
        # Prepare for import
        Partner = self.env['res.partner']
        
        # Statistics
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'companies_created': 0,
        }
        
        # Process each line
        for line in lines_to_import:
            # Prepare partner values
            partner_vals = {
                'name': line.name,
                'is_company': False,
                'type': 'contact',
            }
            
            # Add optional fields if they have values
            if line.phone:
                partner_vals['phone'] = line.phone
                
            if line.email:
                partner_vals['email'] = line.email
                
            if line.notes:
                partner_vals['comment'] = line.notes
                
            if line.employee_id:
                partner_vals['barcode'] = line.employee_id
            
            # Handle company/parent
            if line.company and line.company != 'PRIVATE' and line.company != 'SELF':
                # Check if company exists
                company = Partner.search([
                    ('name', '=', line.company),
                    ('is_company', '=', True)
                ], limit=1)
                
                if not company and self.create_companies:
                    # Create new company
                    company = Partner.create({
                        'name': line.company,
                        'is_company': True,
                        'type': 'contact',
                    })
                    stats['companies_created'] += 1
                
                if company:
                    partner_vals['parent_id'] = company.id
            
            # Check if partner already exists
            domain = [('name', '=', line.name)]
            if line.employee_id:
                domain = ['|', ('barcode', '=', line.employee_id)] + domain
                
            existing_partner = Partner.search(domain, limit=1)
            
            if existing_partner and line.status == 'conflict':
                # Update existing partner if conflict was approved
                existing_partner.write(partner_vals)
                stats['updated'] += 1
                line.write({'result': 'updated'})
            elif not existing_partner:
                # Create new partner
                Partner.create(partner_vals)
                stats['created'] += 1
                line.write({'result': 'created'})
            else:
                stats['skipped'] += 1
                line.write({'result': 'skipped'})
        
        # Update state
        self.write({'state': 'import'})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
