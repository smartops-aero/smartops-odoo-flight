from odoo import api, fields, models


class ResCountry(models.Model):
    """ICAO location-indicator prefixes per country, so a FIR/aerodrome code
    from a flight plan can be resolved to the country it belongs to.

    A code (e.g. ``UAII``, ``UZTR``, ``EHAM``) starts with an ICAO nationality
    prefix — usually two letters, sometimes one (``K`` = USA) or three where a
    region is shared (``UAF`` = Kyrgyzstan vs ``UAA…`` = Kazakhstan).
    Resolution is longest-prefix-match; there are no broad catch-alls, so an
    unmapped code resolves to no country (skipped) rather than a wrong one.

    The table is seeded from ``data/res.country.csv`` (the official Astana Air
    location-indicator list, cross-checked against ``airportsdata`` by
    ``data/generate_aerodrome_and_runway_csvs.py``). Because the country
    records belong to ``base`` (loaded ``noupdate="1"``), Odoo skips the CSV on
    plain ``-u flight`` upgrades; a version-pinned migration reloads it in
    ``mode='init'`` to force the values through — see
    ``migrations/18.0.1.5.2/post-migrate.py``.
    """

    _inherit = "res.country"

    icao_prefixes = fields.Char(
        string="ICAO Prefixes",
        help=(
            "Space-separated ICAO location-indicator prefixes that belong to "
            "this country, used to resolve overflown FIRs and aerodrome codes "
            "to countries. Longest match wins."
        ),
    )

    @api.model
    def _icao_prefix_map(self):
        """Return ``{prefix: country_id}`` for every country with prefixes set.

        Read with ``sudo`` so callers resolving codes get the full mapping
        regardless of their own record rules on res.country.
        """
        prefix_map = {}
        countries = self.sudo().search([("icao_prefixes", "!=", False)])
        for country in countries:
            for token in country.icao_prefixes.replace(",", " ").split():
                token = token.strip().upper()
                if token:
                    prefix_map[token] = country.id
        return prefix_map

    @api.model
    def _countries_for_icao_codes(self, icao_codes):
        """Resolve ICAO codes (e.g. FIR identifiers) to a ``res.country`` set.

        Longest-prefix matching against ``icao_prefixes``; first-appearance
        order kept, duplicates removed, unmatched codes skipped.
        """
        prefix_map = self._icao_prefix_map()
        ordered_ids = []
        seen = set()
        for code in icao_codes:
            token = (code or "").strip().upper()
            if not token:
                continue
            for length in range(len(token), 0, -1):
                country_id = prefix_map.get(token[:length])
                if country_id:
                    if country_id not in seen:
                        seen.add(country_id)
                        ordered_ids.append(country_id)
                    break
        return self.browse(ordered_ids)
