from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BaseImportPipeline(models.Model):
    _name = "base.import.pipeline"
    _description = "Base Import Pipeline"
    
    name = fields.Char(required=True)
    implementation = fields.Selection(
        selection=lambda self: self._selection_implementation(),
        required=True,
    )
    # TODO: Not sure if this is needed, I could not find any use-case yet. Added as I noted we need it
    model_id = fields.Many2one('ir.model', string='Target Model', required=True, ondelete='cascade')
    active = fields.Boolean(default=True)
    result_ids = fields.One2many('base.import.pipeline.result', 'pipeline_id', string='Import Results')
    
    def _dispatch(self, method_name, *args, **kwargs):
        """Dispatch method calls to the appropriate implementation"""
        if hasattr(self, f'_{self.implementation}_{method_name}'):
            method = getattr(self, f'_{self.implementation}_{method_name}')
            return method(*args, **kwargs)
        raise NotImplementedError(
            _("Method %s not implemented for %s") % (method_name, self.implementation)
        )
    
    @api.model
    def _selection_implementation(self):
        """Get all available implementations"""
        implementations = []
        for implementation in self._get_available_implementations():
            implementations.append(implementation)
        return implementations

    @api.model
    def _get_available_implementations(self):
        """Hook method for registering import implementations"""
        return []
    
    def run_import(self, **kwargs):
        """Run the implementation-specific import process
        
        This is just a skeleton that should be overridden by module that
        adds actual import logic.
        """
        result = {
            'created': [],
            'errors': [],
        }
        
        # Log result
        self._log_import_result(result)
        
        return result
    
    def _log_import_result(self, result):
        """Log import result to the database"""
        records_created = len(result.get('created', []))
        errors = result.get('errors', [])
        
        self.env['base.import.pipeline.result'].create({
            'pipeline_id': self.id,
            'date': fields.Datetime.now(),
            'summary': str(result),
            'records_created': records_created,
            'status': 'success' if not errors else 'error',
            'log': '\n'.join(errors) if errors else '',
        })
