import werkzeug
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.osv import expression


class WebsiteFlight(http.Controller):
    def _get_aircraft_domain(self, search=None):
        """Helper to compute domain for aircraft search"""
        domain = request.website.website_domain()
        if not request.env.user.has_group("flight.group_flight_manager"):
            domain = expression.AND([domain, [("website_published", "=", True)]])

        if search:
            search_domain = [
                "|",  # First OR
                "|",  # Second OR
                ("registration", "ilike", search),
                ("model_id.name", "ilike", search),
                ("website_short_description", "ilike", search),
            ]
            domain = expression.AND([domain, search_domain])
        return domain

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
        Aircraft = request.env["flight.aircraft"]

        # Compute domain
        domain = self._get_aircraft_domain(search)
        if model:
            domain = expression.AND([domain, [("model_id", "=", model.id)]])

        # Search aircrafts
        search_url = "/fleet"
        aircraft_url = QueryURL(search_url, ["model", "search"])
        aircraft_count = Aircraft.search_count(domain)

        # Setup pager
        pager = request.website.pager(
            url=search_url,
            total=aircraft_count,
            page=page,
            step=12,
            url_args=post,
        )

        # Search aircrafts with given criteria
        aircrafts = Aircraft.search(domain, limit=12, offset=pager["offset"])

        # Get all aircraft models for filtering
        models = request.env["flight.aircraft.model"].search([])

        values = {
            "aircrafts": aircrafts,
            "pager": pager,
            "aircraft_url": aircraft_url,
            "search": search,
            "search_count": aircraft_count,
            "models": models,
            "selected_model": model,
            "bins": [],
        }

        if not values.get("bins"):
            values["bins"] = []

        return request.render("website_flight_fleet.page_fleet", values)

    @http.route(
        [
            """/aircraft/<model("flight.aircraft"):aircraft>""",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def aircraft(self, aircraft, **kwargs):
        if not aircraft.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()

        # Get the previous and next aircraft based on registration
        Aircraft = request.env["flight.aircraft"]
        domain = self._get_aircraft_domain()

        # Get neighbor aircrafts for navigation
        all_aircraft_ids = Aircraft.search(domain).ids
        current_aircraft_index = all_aircraft_ids.index(aircraft.id)
        prev_aircraft = None
        next_aircraft = None

        if current_aircraft_index > 0:
            prev_aircraft = Aircraft.browse(
                all_aircraft_ids[current_aircraft_index - 1]
            )
        if current_aircraft_index < len(all_aircraft_ids) - 1:
            next_aircraft = Aircraft.browse(
                all_aircraft_ids[current_aircraft_index + 1]
            )

        # Get related aircrafts (same model)
        related_aircraft_domain = expression.AND(
            [
                domain,
                [("model_id", "=", aircraft.model_id.id), ("id", "!=", aircraft.id)],
            ]
        )
        related_aircrafts = Aircraft.search(related_aircraft_domain, limit=4)

        values = {
            "main_object": aircraft,
            "aircraft": aircraft,
            "prev_aircraft": prev_aircraft,
            "next_aircraft": next_aircraft,
            "related_aircrafts": related_aircrafts,
        }

        if aircraft.env.context.get("enable_editor"):
            values.update(enable_editor=True)

        return request.render("website_flight_fleet.page_aircraft_detail", values)

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
        Aircraft = request.env["flight.aircraft"]
        domain = self._get_aircraft_domain(term)
        aircrafts = Aircraft.search(domain, limit=5)

        results = []
        for aircraft in aircrafts:
            results.append(
                {
                    "id": aircraft.id,
                    "name": aircraft.registration,
                    "model": aircraft.model_id.name if aircraft.model_id else "",
                    "url": aircraft.website_url,
                }
            )
        return results
