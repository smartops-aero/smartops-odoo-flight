# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, _

class WebsiteSnippetFilter(models.Model):
    _inherit = 'website.snippet.filter'

    def _get_hardcoded_sample(self, model):
        samples = super()._get_hardcoded_sample(model)
        if model._name == 'flight.aircraft.image':
            data = [{
                'name': _('Boeing 747 Exterior'),
                'description': _('Majestic view of our flagship aircraft'),
                'image': '/website_flight_fleet/static/src/img/aircraft1.jpg',
                'sequence': 1,
            }, {
                'name': _('Airbus A320 Cockpit'),
                'description': _('State-of-the-art flight deck'),
                'image': '/website_flight_fleet/static/src/img/aircraft2.jpg',
                'sequence': 2,
            }, {
                'name': _('Private Jet Interior'),
                'description': _('Luxury cabin configuration'),
                'image': '/website_flight_fleet/static/src/img/aircraft3.jpg',
                'sequence': 3,
            }]
            
            # Merge with existing samples or use new data if no samples
            if samples:
                merged = []
                for index in range(0, max(len(samples), len(data))):
                    merged.append({**samples[index % len(samples)], **data[index % len(data)]})
                samples = merged
            else:
                samples = data
                
        return samples