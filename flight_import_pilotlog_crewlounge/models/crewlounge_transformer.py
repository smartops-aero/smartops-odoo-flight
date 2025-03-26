# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class FlightImportTransformer(models.Model):
    _inherit = "flight.import.transformer"

    @api.model
    def _get_available_implementations(self):
        """Add CrewLounge to available implementations"""
        implementations = super(FlightImportTransformer, self)._get_available_implementations()
        return implementations + [('crewlounge', 'CrewLounge Format')]

    def flight_flight_crewlounge_transform_data(self, data_rows, headers):
        """Transform CrewLounge data to flight.flight format
        
        Args:
            data_rows: List of data rows to transform
            headers: Headers for the data rows
            
        Returns:
            Transformed data with headers as first row
        """
        _logger.info("Starting transformation of CrewLounge data with %d rows", len(data_rows))
        
        # Define the transformed headers we want in our output
        transformed_headers = [
            'id', 'date', 'aircraft_id/registration', 'departure_id/icao', 'arrival_id/icao',
            'pilot_id/id', 'remarks'
        ]
        
        # Create a mapping of original headers to their indices
        header_map = {}
        if headers:
            for idx, col in enumerate(headers):
                header_map[col.upper()] = idx
            _logger.info("Created header map: %s", header_map)
        
        # Create the result with headers as the first row
        transformed_data = [transformed_headers]
        
        # Process each row of the original data
        for idx, row in enumerate(data_rows):
            # Skip header row if present in data_rows
            if idx == 0 and headers and row == headers:
                continue
                
            # Skip empty rows
            if not row or all(not cell for cell in row):
                continue
                
            # Make sure row has enough elements
            if len(row) < max(header_map.values()) + 1 if header_map else 1:
                _logger.warning("Row %d has insufficient columns, skipping", idx)
                continue
                
            # Generate a unique ID for this flight
            flight_id = f"flight_import_{idx:03d}"
            
            # Extract and format date
            date_str = ''
            date_idx = header_map.get('PILOTLOG_DATE', 0)
            if date_idx < len(row) and row[date_idx]:
                try:
                    date_str = datetime.strptime(row[date_idx], '%d-%m-%Y').strftime('%Y-%m-%d')
                except (ValueError, TypeError) as e:
                    _logger.warning("Failed to parse date '%s': %s", row[date_idx] if date_idx < len(row) else 'N/A', e)
            
            # Extract other basic fields with safety checks
            aircraft_reg = ''
            reg_idx = header_map.get('AC_REG')
            if reg_idx is not None and reg_idx < len(row):
                aircraft_reg = row[reg_idx] or ''
                
            departure = ''
            dep_idx = header_map.get('AF_DEP')
            if dep_idx is not None and dep_idx < len(row):
                departure = row[dep_idx] or ''
                
            arrival = ''
            arr_idx = header_map.get('AF_ARR')
            if arr_idx is not None and arr_idx < len(row):
                arrival = row[arr_idx] or ''
                
            remarks = ''
            rem_idx = header_map.get('REMARKS')
            if rem_idx is not None and rem_idx < len(row):
                remarks = row[rem_idx] or ''
            
            # Use base_pilot_id from import context if available
            pilot_id = ''
            if self.env.context.get('base_pilot_id'):
                pilot_id = str(self.env.context.get('base_pilot_id'))
            
            # Create a transformed row with all required fields
            transformed_row = [
                flight_id,
                date_str,
                aircraft_reg,
                departure,
                arrival,
                pilot_id,
                remarks
            ]
            
            # Add this row to our transformed data
            transformed_data.append(transformed_row)
        
        _logger.info("Transformation complete, generated %d rows", len(transformed_data))
        return transformed_data
