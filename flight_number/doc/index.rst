=============
Flight Number
=============

Add standardized flight numbers and prefixes to flight operations in Odoo 18.

Overview
========

Simple extension that adds flight number and prefix fields to the Flight module. Assign standard aviation identifiers like "AA123" or configure custom prefixes for your operations.

Features
========

- **Flight Numbers**: Add flight number fields to flight records
- **Custom Prefixes**: Configure flight prefixes for operators, routes, or flight types

Installation
============

1. Install from Odoo Apps menu
2. Requires: ``base``, ``flight`` modules

Usage
=====

Configure Prefixes
------------------

1. Go to **Flights → Configuration → Flight Prefixes**
2. Create prefixes (e.g., "AA" for American Airlines, "CHT" for Charter)

Assign Flight Numbers
---------------------

1. Open any **Flight** record
2. Select a prefix (optional)
3. Enter the flight number

Module Structure
================

::

    flight_number/
    ├── models/
    │   ├── flight_flight.py     # Extends flight model with number fields
    └── flight_number.py      # Flight prefix configuration
    └── views/
        ├── flight_views.xml      # Flight form enhancements
        ├── flight_number_views.xml
        └── flight_prefix_views.xml

Example Use Cases
=================

- **Commercial Operations**: Track flights with standard airline flight numbers
- **Charter Services**: Assign unique identifiers to charter flights
- **Multi-Operator**: Use prefixes to distinguish between different operators

Technical Details
=================

- **Simple Extension**: Focused module that adds exactly what's needed
- **Integration**: Seamlessly extends core Flight module
- **Flexible**: Prefixes are optional, flight numbers can be used standalone

Support
=======

- **Author**: Apexive Solutions LLC
- **Website**: https://github.com/smartops-aero/smartops-odoo-flight
- **License**: LGPL-3
