import werkzeug
import logging
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.osv import expression
_logger = logging.getLogger(__name__)

class WebsiteFlight(http.Controller):
    def _get_base_domain(self):
        """Helper to compute domain for aircraft search"""
        domain = request.website.website_domain()
        if not request.env.user.has_group("flight.group_flight_manager"):
            domain = expression.AND([domain, [("website_published", "=", True)]])
        return domain

    def _get_search_domain(self, search=None):
        """Build search domain for aircraft with optional search term"""
        domain = self._get_base_domain()
        
        if search:
            search_domain = [
                "|",
                "|",
                ("registration", "ilike", search),
                ("model_id.name", "ilike", search),
                ("website_short_description", "ilike", search),
            ]
            domain = expression.AND([domain, search_domain])
        return domain


    def _prepare_fleet_values(self, page=1, model=None, search=None, **post):
        """Prepare values for fleet page rendering"""
        Aircraft = request.env["flight.aircraft"]
        domain = self._get_search_domain(search)
        
        if model:
            domain = expression.AND([domain, [("model_id", "=", model.id)]])

        # Search configuration
        url = "/fleet"
        aircraft_url = QueryURL(url, ["model", "search"])
        aircraft_count = Aircraft.search_count(domain)

        # Pager setup
        pager = request.website.pager(
            url=url,
            total=aircraft_count,
            page=page,
            step=12,
            url_args=post,
        )

        # Get aircrafts
        aircrafts = Aircraft.search(domain, limit=12, offset=pager["offset"])
        models = request.env["flight.aircraft.model"].search([])

        return {
            "aircrafts": aircrafts,
            "pager": pager,
            "aircraft_url": aircraft_url,
            "search": search,
            "search_count": aircraft_count,
            "models": models,
            "selected_model": model,
            "bins": [],
        }

    @http.route(
        [
            "/fleet",
            "/fleet/page/<int:page>",
            '/fleet/model/<model("flight.aircraft.model"):model>',
            '/fleet/model/<model("flight.aircraft.model"):model>/page/<int:page>',
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def fleet(self, page=1, model=None, search=None, **post):
        """Display fleet listing page with optional filtering and search"""
        values = self._prepare_fleet_values(page, model, search, **post)
        return request.render("website_flight_fleet.page_fleet", values)

    @http.route(['/aircraft/<model("flight.aircraft"):aircraft>'], type='http', auth="public", website=True)
    def aircraft_detail(self, aircraft, **kwargs):        
        values = {
            'aircraft': aircraft,
            'main_object': aircraft,
            'is_website_editor': request.env.user.has_group('website.group_website_publisher'),
        }
        
        response = request.render("website_flight_fleet.page_aircraft_detail", values)
        return response

    @http.route(
        '/fleet/aircraft/json/<model("flight.aircraft"):aircraft>',
        type="json",
        auth="public",
        website=True,
    )
    def aircraft_json(self, aircraft, **kw):
        """Return specific aircraft data in JSON format"""
        return {
            "registration": aircraft.registration,
            "model": aircraft.model_id.name if aircraft.model_id else False,
            "website_published": aircraft.website_published,
            "website_url": aircraft.website_url,
        }

    @http.route("/fleet/search", type="json", auth="public", website=True)
    def fleet_search(self, term, **kwargs):
        """Return search suggestions for aircraft"""
        domain = self._get_search_domain(term)
        Aircraft = request.env["flight.aircraft"]
        aircrafts = Aircraft.search(domain, limit=5)

        results = [{
            "id": aircraft.id,
            "name": aircraft.registration,
            "model": aircraft.model_id.name if aircraft.model_id else "",
            "url": aircraft.website_url,
        } for aircraft in aircrafts]
        return results
