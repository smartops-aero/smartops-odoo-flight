{
    "name": "Flight UOM",
    "summary": "Aviation-specific units of measurement for flight operations",
    "description": """
Flight UOM Module
=================

This module adds aviation-specific units of measurement essential for flight operations.

Distance Units:
---------------
* Nautical Miles (nm) - Standard aviation distance measurement
* Statute Miles (mi) - Alternative distance measurement
* Kilometers (km) - Metric distance measurement

Speed Units:
------------
* Knots (kt) - Standard aviation speed (nautical miles per hour)
* Kilometers per hour (kph) - Metric speed measurement
* Feet per second (fps) - Vertical speed measurement

The module provides two new UOM categories:
* Distance - For aviation-specific distance measurements
* Speed - For aviation-specific speed measurements

All conversion factors follow international aviation standards.
    """,
    "author": "Apexive Solutions LLC",
    "website": "https://github.com/smartops-aero/smartops-odoo-flight",
    "license": "LGPL-3",
    "category": "Industries",
    "version": "18.0.1.0.0",
    "depends": [
        "uom",
    ],
    "data": [
        "data/product_uom_data.xml",
    ],
    "images": [
        "static/description/banner.jpeg",
    ],
    "installable": True,
    "auto_install": False,
}
