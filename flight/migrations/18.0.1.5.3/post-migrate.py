# Copyright 2025 Apexive <https://apexive.com/>
# License MIT (https://opensource.org/licenses/MIT).

import logging

from odoo import SUPERUSER_ID, api
from odoo.tools.convert import convert_file

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Force-reapply the ICAO prefixes onto ``res.country``.

    The country records are owned by ``base``, which loads them with
    ``<data noupdate="1">``. That flag makes Odoo skip flight's
    ``data/res.country.csv`` on every ``-u flight`` after the very first
    install, so later edits to the prefix table never reach the database
    (Russia keeps the stale single-letter ``U`` from the original load, and
    rows added afterwards such as Brunei ``WB`` stay empty).

    Reloading the file in ``mode='init'`` ignores the noupdate flag and writes
    the current values. Whenever ``data/res.country.csv`` changes again, bump
    the module version and re-point (copy) this migration to the new version so
    the change actually lands on existing databases.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Force-reapplying ICAO prefixes from data/res.country.csv")
    convert_file(
        env,
        "flight",
        "data/res.country.csv",
        None,
        mode="init",
        noupdate=False,
        kind="data",
    )
    _logger.info("ICAO prefixes reapplied to res.country")
