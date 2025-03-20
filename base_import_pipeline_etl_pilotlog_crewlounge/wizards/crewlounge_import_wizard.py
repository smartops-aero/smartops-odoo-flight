import base64
import csv
import io

from odoo import _, fields, models
from odoo.exceptions import UserError

IMPLEMENTATION = "pilotlog_crewlounge"

class CrewLoungeImportWizard(models.TransientModel):
    _name = "crewlounge.import.wizard"
    _description = "CrewLounge Import Wizard"

    file = fields.Binary(string="CSV File", required=True)
    filename = fields.Char(string="Filename")
    delimiter = fields.Char(
        string="Delimiter", default=",", required=True, help="CSV delimiter character"
    )

    # Post-process settings
    batch_size = fields.Integer(
        string="Batch Size",
        default=500,
        help="Number of records to process in each batch during load, post-processing. Higher values are faster but use more memory.",
    )

    # Pilot selection
    partner_id = fields.Many2one(
        "res.partner",
        string="Pilot",
        required=True,
        domain=[("is_company", "=", False)],
        help="Select the pilot for whom this flight data is being imported",
    )

    # Preview fields
    preview_data = fields.Text(string="Preview Info", readonly=True)
    preview_row_count = fields.Integer(string="Total Rows", readonly=True)
    preview_column_count = fields.Integer(string="Total Columns", readonly=True)
    preview_column_names = fields.Text(string="Column Names", readonly=True)

    # Result fields
    result_data = fields.Text(string="Import Results", readonly=True)
    created_count = fields.Integer(string="Created Records", readonly=True)
    updated_count = fields.Integer(string="Updated Records", readonly=True)
    error_count = fields.Integer(string="Errors", readonly=True)

    # State management
    state = fields.Selection(
        [
            ("upload", "Upload"),
            ("preview", "Preview"),
            ("completed", "Completed"),
        ],
        string="State",
        default="upload",
        required=True,
    )

    def action_back_to_upload(self):
        """Go back to the upload state"""
        self.ensure_one()
        self.state = "upload"
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_preview(self):
        """Preview the CSV data before importing"""
        self.ensure_one()

        if not self.file:
            raise UserError(_("Please upload a CSV file"))

        try:
            # Decode the file content
            content = base64.b64decode(self.file).decode("utf-8")

            # First count total rows in the CSV
            row_count = (
                sum(
                    1
                    for _ in csv.reader(io.StringIO(content), delimiter=self.delimiter)
                )
                - 1
            )  # Subtract header row

            # Parse CSV for preview
            reader = csv.DictReader(io.StringIO(content), delimiter=self.delimiter)

            # Get the first 5 rows for preview
            preview_rows = []
            for i, row in enumerate(reader):
                if i >= 5:  # Limit to 5 rows
                    break
                preview_rows.append(row)

            if preview_rows:
                # Get all keys from the first row
                keys = list(preview_rows[0].keys())

                # Store the structured data
                self.preview_row_count = row_count
                self.preview_column_count = len(keys)
                self.preview_column_names = ", ".join(keys)

                # Simple text summary
                message = "Found %s rows with %s columns.\n\nColumn names: %s\n\nThe file appears to be valid and ready for import."
                self.preview_data = _(message) % (
                    row_count,
                    len(keys),
                    self.preview_column_names,
                )
            else:
                self.preview_data = _("No data found in the CSV file")

            pipeline = self.env["base.import.pipeline"].search(
                [("implementation", "=", IMPLEMENTATION)], limit=1
            )

            if pipeline and not self.batch_size:
                self.batch_size = pipeline.batch_size

            self.state = "preview"

            return {
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
            }

        except Exception as e:
            raise UserError(_("Error previewing data: %s") % str(e))

    def action_import(self):
        """Import the CSV file using the CrewLounge import pipeline"""
        self.ensure_one()

        if not self.file:
            raise UserError(_("Please upload a CSV file"))

        # Get the CrewLounge import pipeline
        pipeline = self.env["base.import.pipeline"].search(
            [("implementation", "=", IMPLEMENTATION)], limit=1
        )

        if not pipeline:
            raise UserError(
                _("CrewLounge import pipeline not found. Please create one first.")
            )

        # Run the import with the file content, filename, and delimiter as parameters
        result = pipeline.with_context(import_partner_id=self.partner_id.id).run_import(
            file_content=self.file,
            filename=self.filename,
            csv_delimiter=self.delimiter,
            batch_size=self.batch_size or pipeline.batch_size,
        )

        # Store the results
        self.created_count = len(result.get("created", []))
        self.updated_count = len(result.get("updated", []))
        self.error_count = len(result.get("errors", []))

        # Create detailed result information
        message = _("Import completed successfully.\n\n")
        message += _("• %s flights created\n") % self.created_count
        message += _("• %s flights updated\n") % self.updated_count

        if self.error_count:
            message += _("• %s errors occurred\n\n") % self.error_count
            message += _("Error details:\n")
            for error in result.get("errors", [])[:10]:  # Show first 10 errors
                message += f"- {error}\n"
            if len(result.get("errors", [])) > 10:
                message += _("(and %s more errors)") % (
                    len(result.get("errors", [])) - 10
                )

        self.result_data = message

        # Change state to completed
        self.state = "completed"

        # Show the wizard with the results
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_new_import(self):
        """Reset the wizard to start a new import"""
        self.ensure_one()
        self.state = "upload"
        self.file = False
        self.filename = False
        self.preview_data = False
        self.result_data = False
        self.created_count = False
        self.updated_count = False
        self.error_count = False

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
