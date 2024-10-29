from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class PortalFlight(portal.CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "flight_count" in counters:
            flight_count = (
                request.env["flight.flight"]
                .sudo()
                .search_count(self._prepare_flights_domain())
            )
            values["flight_count"] = flight_count
        return values

    def _prepare_flights_domain(self):
        return []

    def _get_flight_domain(self, page=1, date_begin=None, date_end=None, sortby=None):
        domain = self._prepare_flights_domain()
        if date_begin and date_end:
            domain += [("date", ">=", date_begin), ("date", "<=", date_end)]
        return domain

    @http.route(
        ["/my/flights", "/my/flights/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_flights(
        self, page=1, date_begin=None, date_end=None, sortby=None, **kw
    ):
        values = self._prepare_portal_layout_values()
        FlightFlight = request.env["flight.flight"]

        domain = self._get_flight_domain(page, date_begin, date_end, sortby)

        searchbar_sortings = {
            "date": {"label": "Date", "order": "date desc"},
            "departure": {"label": "Departure", "order": "departure_id"},
            "arrival": {"label": "Arrival", "order": "arrival_id"},
        }

        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        flight_count = FlightFlight.search_count(domain)
        pager = portal_pager(
            url="/my/flights",
            url_args={"date_begin": date_begin, "date_end": date_end, "sortby": sortby},
            total=flight_count,
            page=page,
            step=self._items_per_page,
        )

        flights = FlightFlight.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )

        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "flights": flights,
                "page_name": "flight",
                "default_url": "/my/flights",
                "pager": pager,
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("flight_portal.portal_my_flights", values)

    @http.route(
        ["/my/flight/<int:flight_id>"], type="http", auth="public", website=True
    )
    def portal_flight_page(self, flight_id, access_token=None, **kw):
        try:
            flight_sudo = self._document_check_access(
                "flight.flight", flight_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        values = {
            "page_name": "flight",
            "flight": flight_sudo,
        }
        return request.render("flight_portal.portal_flight_page", values)
