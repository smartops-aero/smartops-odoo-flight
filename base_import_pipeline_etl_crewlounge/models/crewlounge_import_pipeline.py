import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BaseImportPipeline(models.Model):
    _inherit = "base.import.pipeline"

    def _selection_implementation(self):
        selection = super()._selection_implementation()
        selection.append(("crewlounge", "Flight Import - CrewLounge"))
        return selection

    def _crewlounge_extract(
        self, file_content, filename=None, csv_delimiter=",", **kwargs
    ):
        """Extract data from CrewLounge CSV file"""
        if not file_content:
            raise UserError(_("No file content provided"))

        # Use the CSV extraction helper method
        return self.env["base.import.pipeline"]._extract_from_csv(
            file_content, filename, delimiter=csv_delimiter
        )

    def _prepare_update_values(self, target_model, record, values):
        """Override to handle special case for flight.event.time model updates
        
        For flight.event.time, we only want to update the time field
        to respect the constraint in the write method
        """
        if target_model == "flight.event.time" and "time" in values:
            # Only keep the time field for flight.event.time model
            return {"time": values["time"]}
        
        # For all other models, use the standard implementation
        return super()._prepare_update_values(target_model, record, values)

