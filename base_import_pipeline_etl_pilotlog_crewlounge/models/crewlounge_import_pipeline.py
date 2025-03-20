import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BaseImportPipeline(models.Model):
    _inherit = "base.import.pipeline"

    def _selection_implementation(self):
        selection = super()._selection_implementation()
        selection.append(("pilotlog_crewlounge", "Flight Import - CrewLounge"))
        return selection

    def _pilotlog_crewlounge_extract(
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

    def _is_zero_value(self, value):
        """Determine if a value should be considered as zero/null/empty
        
        Returns True if the value is:
        - None
        - False
        - Empty string
        - Integer zero (0)
        - Float zero (0.0)
        - String representation of zero ("0")
        
        This is used to skip creating records with zero counts, durations, or times.
        """
        # Check for None, False, or empty string
        if value is None or value is False or value == "":
            return True
            
        # Check by type for more precise comparison
        value_type = type(value)
        
        # Integer comparison
        if value_type is int:
            return value == 0
            
        # Float comparison
        if value_type is float:
            return value == 0.0
            
        # String comparison - strip whitespace and check for "0"
        if value_type is str:
            stripped = value.strip()
            return stripped == "0" or stripped == ""
            
        # For any other types, try to convert to float if possible
        try:
            return float(value) == 0
        except (ValueError, TypeError):
            # If we can't convert to float, it's not a zero value
            return False

    def _build_post_process_values_and_domain(
        self, parent_record, target_model, mappings, extracted_data
    ):
        """Override to implement validation checks for pilot events and times
        
        - Skip flight.pilot.event if count is 0
        - Skip flight.pilot.time if duration is 0.0
        - Skip flight.event.time if time is 0.0
        """
        values, domain = super()._build_post_process_values_and_domain(
            parent_record, target_model, mappings, extracted_data
        )
        
        # Skip flight.pilot.event records with count 0
        if target_model == "flight.pilot.event" and self._is_zero_value(values.get("count")):
            _logger.info(f"Skipping pilot event record with zero count: {values}")
            return {}, []
            
        # Skip flight.pilot.time records with duration 0.0
        if target_model == "flight.pilot.time" and self._is_zero_value(values.get("duration")):
            _logger.info(f"Skipping pilot time record with zero duration: {values}")
            return {}, []
            
        # Skip flight.event.time records with time 0.0
        if target_model == "flight.event.time" and self._is_zero_value(values.get("time")):
            _logger.info(f"Skipping flight event time record with zero time: {values}")
            return {}, []
            
        return values, domain
