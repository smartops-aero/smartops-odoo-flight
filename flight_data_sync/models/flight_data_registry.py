# Copyright 2024 Apexive <https://apexive.com/>

from odoo import api, fields, models


class FlightDataRegistry(models.Model):
    _name = "flight.data.registry"
    _description = "Flight Data Registry"

    provider_id = fields.Many2one(
        "flight.data.provider", string="Data Provider", required=True
    )
    model = fields.Selection(
        selection="_selection_model", string="Model", required=True
    )
    local_id = fields.Integer(string="Local ID", required=True)
    external_id = fields.Char(string="External ID", required=True)
    external_provider_id = fields.Char(string="External Provider ID", required=True)

    _sql_constraints = [
        (
            "unique_registry_entry",
            "unique(provider_id, model, external_id)",
            "A registry entry with this provider, model, and external ID already exists.",
        ),
    ]

    @api.model
    def _selection_model(self):
        return self.env["flight.data.provider"]._get_available_sync_models()

    @api.model
    def get_or_create_local_id(
        self, provider_id, model, external_id, external_provider_id, values
    ):
        registry_entry = self.search(
            [
                ("provider_id", "=", provider_id),
                ("model", "=", model),
                ("external_id", "=", external_id),
            ],
            limit=1,
        )

        if registry_entry:
            return registry_entry.local_id

        Model = self.env[model]
        record = Model.create(values)

        self.create(
            {
                "provider_id": provider_id,
                "model": model,
                "local_id": record.id,
                "external_id": external_id,
                "external_provider_id": external_provider_id,
            }
        )

        return record.id

    @api.model
    def get_local_id(self, provider_id, model, external_id):
        registry_entry = self.search(
            [
                ("provider_id", "=", provider_id),
                ("model", "=", model),
                ("external_id", "=", external_id),
            ],
            limit=1,
        )

        return registry_entry.local_id if registry_entry else False
