{
    "name": "Aircraft Amenities",
    "category": "Flight",
    "sequence": 196,
    "summary": "Manage aircraft amenities and comfort features",
    "version": "16.0.1.0.0",
    "depends": ["flight"],
    "data": [
        "security/ir.model.access.csv",
        "views/flight_aircraft_views.xml",
        "views/amenities_menus.xml",
        "data/flight_aircraft_amenity_data.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}