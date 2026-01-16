import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FlightImportPIlotlogTransformer(models.Model):
    _name = "flight.import.pilotlog.transformer"
    _inherit = ["mail.thread"]
    _description = "Flight Import Transformer"

    name = fields.Char(required=True)
    implementation = fields.Selection(
        selection=lambda self: self._selection_implementation(),
        required=True,
    )
    active = fields.Boolean(default=True)
    model_id = fields.Many2one(
        "ir.model",
        string="Target Model",
        required=True,
        ondelete="cascade",
        domain=[
            (
                "model",
                "in",
                [
                    "flight.flight",
                    "flight.aircraft",
                    "flight.aircraft.model",
                    "flight.aircraft.make",
                ],
            )
        ],
        help="The model that this transformer will import data into",
    )

    def _dispatch(self, method, *args, **kwargs):
        """Dispatch method call to appropriate implementation"""
        if not self.implementation:
            raise UserError(_("Transformer implementation not configured"))

        # Get model name from model_id and convert to snake_case format
        model_name = self.model_id.model.replace(".", "_")

        # Try model-specific implementation first
        impl_method = f"{model_name}_{self.implementation}_{method}"
        if hasattr(self, impl_method):
            return getattr(self, impl_method)(*args, **kwargs)

        # Fall back to generic implementation
        impl_method = f"{self.implementation}_{method}"
        if not hasattr(self, impl_method):
            raise NotImplementedError(
                _("Method %s not implemented for implementation %s on model %s")
                % (method, self.implementation, self.model_id.model)
            )

        return getattr(self, impl_method)(*args, **kwargs)

    @api.model
    def _selection_implementation(self):
        """Get all available implementations from transformer implementations"""
        implementations = []
        for impl in self._get_available_implementations():
            implementations.append(impl)
        return implementations

    @api.model
    def _get_available_implementations(self):
        """Hook method for registering transformer implementations"""
        return []

    def transform_data(self, data_rows, headers, import_wizard=None):
        """Transform data using this transformer's implementation

        Args:
            data_rows: List of data rows to transform
            headers: Headers for the data rows
            import_wizard: The import wizard record containing configuration

        Returns:
            Transformed data with headers as first row
        """
        return self._dispatch("transform_data", data_rows, headers, import_wizard)
