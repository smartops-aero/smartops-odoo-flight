# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import base64
import csv
import io
import logging
from io import BytesIO

try:
    import xlrd
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FlightDataFileImportMixin(models.AbstractModel):
    """Mixin for handling file imports with different formats.
    
    This mixin provides functionality for importing data from different file formats
    (CSV, XLS, XLSX) with configurable options like delimiters for CSV files.
    """
    _name = "flight.data.file.import.mixin"
    _description = "Flight Data File Import Mixin"
    _inherit = ["flight.data.import.mixin"]

    # File import fields
    import_file = fields.Binary(
        string="Import File",
        required=True,
        help="Select a file to import",
    )
    filename = fields.Char("Filename")
    
    # File format options
    file_format = fields.Selection([
        ('auto', 'Auto-detect'),
        ('csv', 'CSV'),
        ('xls', 'XLS'),
        ('xlsx', 'XLSX'),
    ], string="File Format", default='auto', required=True,
        help="Select the format of the import file")
    
    # CSV options
    csv_delimiter = fields.Selection([
        (';', 'Semicolon (;)'),
        (',', 'Comma (,)'),
        ('\t', 'Tab'),
        ('|', 'Pipe (|)'),
    ], string="CSV Delimiter", default=';', required=True,
        help="Select the delimiter used in the CSV file")
    
    csv_quotechar = fields.Selection([
        ('"', 'Double Quote (")'),
        ("'", "Single Quote (')"),
    ], string="CSV Quote Character", default='"', required=True,
        help="Select the quote character used in the CSV file")
    
    has_header = fields.Boolean("Has Header", default=True,
        help="Check if the file has a header row")
    
    # Common file import methods
    def _import_file(self):
        """Process the file and prepare data for preview.
        
        This method is similar to the _import_file method in account.statement.import.
        It processes the uploaded file and prepares the data for preview.
        
        Returns:
            dict: Result of the import process containing:
                - imported_ids: List of IDs of imported records
                - notifications: List of text messages
                - total: Total number of rows processed
                - valid: Number of valid rows
                - invalid: Number of invalid rows
                - conflict: Number of rows with conflicts
                - error: Error message if any
        """
        self.ensure_one()
        result = {
            "imported_ids": [],
            "notifications": [],  # list of text messages
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "conflict": 0,
            "error": None,
        }
        
        # This method should be implemented by specific import wizards
        # that inherit from this mixin
        try:
            self._import_single_file(None, result)
        except Exception as e:
            raise UserError(f"Error importing file: {str(e)}")
            
        return result
    
    def action_import_file(self):
        """Process the file chosen in the wizard and return an action.
        
        This method is similar to the import_file_button method in account.statement.import.
        It processes the uploaded file and returns an action to display the results.
        
        Returns:
            dict: Action to display import results
        """
        result = self._import_file()
        
        # Update statistics
        self._update_statistics()
        
        # Update state
        self.state = 'preview'
        
        # Return view
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
    
    # File parsing methods
    @api.model
    def _get_supported_file_extensions(self):
        """Return a list of supported file extensions.
        
        Returns:
            list: List of supported file extensions
        """
        extensions = ['csv']
        if EXCEL_SUPPORT:
            extensions.extend(['xls', 'xlsx'])
        return extensions
    
    def _detect_file_format(self, filename):
        """Detect file format based on filename extension.
        
        Args:
            filename (str): Name of the file
            
        Returns:
            str: Detected file format ('csv', 'xls', 'xlsx')
        """
        if not filename:
            return 'csv'  # Default to CSV if no filename
            
        ext = filename.split('.')[-1].lower()
        if ext == 'csv':
            return 'csv'
        elif ext == 'xls':
            return 'xls'
        elif ext == 'xlsx':
            return 'xlsx'
        else:
            return 'csv'  # Default to CSV for unknown extensions
    
    def _get_parse_options(self):
        """Get standard parsing options based on current settings.
        
        Returns:
            dict: Dictionary with parsing options
        """
        return {
            'delimiter': self.csv_delimiter,
            'quotechar': self.csv_quotechar,
            'has_header': self.has_header,
        }
    
    def _parse_csv_file(self, file_data, options=None):
        """Parse CSV file and return rows as list of lists.
        
        Args:
            file_data (bytes): File content
            options (dict, optional): Parsing options
            
        Returns:
            dict: Parsed data with header and rows
            
        Raises:
            UserError: If there is an error parsing the CSV file
        """
        if options is None:
            options = self._get_parse_options()
            
        delimiter = options.get('delimiter', self.csv_delimiter)
        quotechar = options.get('quotechar', self.csv_quotechar)
        has_header = options.get('has_header', self.has_header)
        
        try:
            # Decode file data
            csv_data = file_data.decode('utf-8')
            reader = csv.reader(
                io.StringIO(csv_data),
                delimiter=delimiter,
                quotechar=quotechar
            )
            
            # Convert to list
            rows = list(reader)
            
            # Remove header if needed
            if has_header and rows:
                header = rows[0]
                data_rows = rows[1:]
                return {'header': header, 'rows': data_rows}
            else:
                return {'header': None, 'rows': rows}
                
        except Exception as e:
            _logger.exception("Error parsing CSV file")
            raise UserError(_("Error parsing CSV file: %s", str(e)))
    
    def _parse_xls_file(self, file_data, options=None):
        """Parse XLS file and return rows as list of lists.
        
        Args:
            file_data (bytes): File content
            options (dict, optional): Parsing options
            
        Returns:
            dict: Parsed data with header and rows
            
        Raises:
            UserError: If Excel support is not available or there is an error parsing the file
        """
        if not EXCEL_SUPPORT:
            raise UserError(_("Excel support is not available. Please install xlrd and openpyxl packages."))
            
        if options is None:
            options = self._get_parse_options()
            
        has_header = options.get('has_header', self.has_header)
        
        try:
            # Read XLS file
            book = xlrd.open_workbook(file_contents=file_data)
            sheet = book.sheet_by_index(0)
            
            # Extract rows
            rows = []
            for row_idx in range(sheet.nrows):
                row = []
                for col_idx in range(sheet.ncols):
                    cell_value = sheet.cell_value(row_idx, col_idx)
                    row.append(str(cell_value))
                rows.append(row)
            
            # Remove header if needed
            if has_header and rows:
                header = rows[0]
                data_rows = rows[1:]
                return {'header': header, 'rows': data_rows}
            else:
                return {'header': None, 'rows': rows}
                
        except Exception as e:
            _logger.exception("Error parsing XLS file")
            raise UserError(_("Error parsing XLS file: %s", str(e)))
    
    def _parse_xlsx_file(self, file_data, options=None):
        """Parse XLSX file and return rows as list of lists.
        
        Args:
            file_data (bytes): File content
            options (dict, optional): Parsing options
            
        Returns:
            dict: Parsed data with header and rows
            
        Raises:
            UserError: If Excel support is not available or there is an error parsing the file
        """
        if not EXCEL_SUPPORT:
            raise UserError(_("Excel support is not available. Please install xlrd and openpyxl packages."))
            
        if options is None:
            options = self._get_parse_options()
            
        has_header = options.get('has_header', self.has_header)
        
        try:
            # Read XLSX file
            workbook = openpyxl.load_workbook(BytesIO(file_data), read_only=True)
            sheet = workbook.active
            
            # Extract rows
            rows = []
            for row in sheet.rows:
                row_values = []
                for cell in row:
                    row_values.append(str(cell.value) if cell.value is not None else "")
                rows.append(row_values)
            
            # Remove header if needed
            if has_header and rows:
                header = rows[0]
                data_rows = rows[1:]
                return {'header': header, 'rows': data_rows}
            else:
                return {'header': None, 'rows': rows}
                
        except Exception as e:
            _logger.exception("Error parsing XLSX file")
            raise UserError(_("Error parsing XLSX file: %s", str(e)))
    
    def _parse_file(self, file_data, filename=None, options=None):
        """Parse file based on format and return rows as list of lists.
        
        Args:
            file_data (bytes): File content
            filename (str, optional): Filename with extension
            options (dict, optional): Parsing options
            
        Returns:
            dict: Parsed data with header and rows
            
        Raises:
            UserError: If the file format is unsupported or there is an error parsing the file
        """
        if options is None:
            options = self._get_parse_options()
            
        # Determine file format
        file_format = self.file_format
        if file_format == 'auto' and filename:
            file_format = self._detect_file_format(filename)
        
        # Parse file based on format
        if file_format == 'csv':
            return self._parse_csv_file(file_data, options)
        elif file_format == 'xls':
            return self._parse_xls_file(file_data, options)
        elif file_format == 'xlsx':
            return self._parse_xlsx_file(file_data, options)
        else:
            raise UserError(_("Unsupported file format: %s", file_format))
    
    # Import methods
    def _import_single_file(self, file_data, result):
        """Import a single file.
        
        This method is called by the _import_file method.
        It parses the file and processes the parsed data.
        
        Args:
            file_data (bytes): File content
            result (dict): Dictionary to store import results
            
        Returns:
            dict: Updated result dictionary
        """
        # Get file data if not provided
        if file_data is None:
            _logger.info("Start to import file %s", self.filename)
            file_data = base64.b64decode(self.import_file)
        
        # Parse the file
        parsed_data = self._parse_file(file_data, self.filename)
        
        # Check if parsed data is valid
        if not self._check_parsed_data(parsed_data):
            result['error'] = _("Could not parse file or no data found")
            return result
        
        # Process the parsed data (to be implemented by specific wizards)
        self._process_parsed_data(parsed_data, result)
        
        return result
    
    def _process_parsed_data(self, parsed_data, result):
        """Process the parsed data and create import lines.
        
        This method should be implemented by specific import wizards.
        It should process the parsed data and create import lines.
        
        Args:
            parsed_data (dict): Parsed data with header and rows
            result (dict): Dictionary to store import results
            
        Example implementation:
        ```
        def _process_parsed_data(self, parsed_data, result):
            header = parsed_data.get('header', [])
            rows = parsed_data.get('rows', [])
            
            # Create import lines
            import_line_vals = []
            for row in rows:
                # Process row and create import line values
                line_vals = {
                    'import_id': self.id,
                    'raw_data': str(row),
                    # Add other fields based on row data
                }
                import_line_vals.append(line_vals)
            
            # Create import lines
            if import_line_vals:
                self.env['your.import.line.model'].create(import_line_vals)
            
            # Update result
            result['total'] = len(rows)
            
            # Validate lines
            for line in self.import_line_ids:
                line.validate()
            
            # Update result with validation results
            result['valid'] = len(self.import_line_ids.filtered(lambda l: l.state == 'valid'))
            result['invalid'] = len(self.import_line_ids.filtered(lambda l: l.state == 'invalid'))
            result['conflict'] = len(self.import_line_ids.filtered(lambda l: l.state == 'conflict'))
        ```
        """
        raise NotImplementedError("This method must be implemented by specific import wizards")
