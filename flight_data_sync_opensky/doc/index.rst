===================================
Flight Data Sync - OpenSky Network
===================================

Synchronize flight data with the OpenSky Network API.

Overview
========

This module integrates Odoo with the OpenSky Network, a non-profit association
providing free access to real-time and historical ADS-B flight data.

Features
========

* Interactive sync wizard with two modes
* Compare OpenSky data with existing Odoo flights
* Choose to create, update, or skip each flight
* Automatic matching by aircraft, date, and route
* View flight times, duration, and callsigns from OpenSky

Configuration
=============

1. Create an OpenSky Network data provider
2. Optionally set username/password for higher API limits
3. Ensure aircraft have ICAO24 addresses set

Usage
=====

From the flight list view:

1. Click Action menu → "Sync with OpenSky Network"
2. Select sync mode (specific flights or aircraft date range)
3. Configure parameters and click "Fetch Flights"
4. Review comparison table and adjust actions
5. Click "Apply Sync" to create/update flights

See README.md for detailed documentation.

License
=======

LGPL-3

Credits
=======

* Apexive Solutions LLC
* OpenSky Network (data provider)
