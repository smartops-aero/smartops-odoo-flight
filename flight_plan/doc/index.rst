===========
Flight Plan
===========

Flight plan routes and waypoints management for Odoo 18.

Overview
========

Manage detailed flight plans including routes, waypoints, and aerodrome sequences. Store and track navigation information for flight planning and operations.

Features
========

- **Flight Plans**: Create detailed flight plans linked to flights
- **Routes**: Define reusable routes with waypoint sequences
- **Waypoints**: Manage navigation waypoints with coordinates
- **Aerodrome Sequences**: Track departure, arrival, and alternate aerodromes
- **JSON Data**: Store detailed navigation data using the JSON widget

Installation
============

1. Install from Odoo Apps menu
2. Requires: ``flight``, ``flight_event``, ``flight_json_widget`` modules

Usage
=====

Create Flight Plans
-------------------

1. Go to **Flights → Flight Plans**
2. Create a new flight plan
3. Link to a flight record
4. Define route or add waypoints

Define Routes
-------------

1. Navigate to **Flights → Configuration → Flight Routes**
2. Create reusable routes
3. Add waypoints in sequence
4. Associate routes with flight plans

Manage Waypoints
----------------

1. Go to **Flights → Configuration → Waypoints**
2. Define waypoints with:

   - Identifier/name
   - Coordinates
   - Navigation data

Module Structure
================

.. code-block:: text

    flight_plan/
    ├── models/
    │   ├── flight_plan.py               # Main flight plan model
    │   ├── flight_plan_route.py         # Reusable routes
    │   ├── flight_route_waypoint.py     # Waypoint definitions
    │   └── flight_plan_aerodrome.py     # Aerodrome sequences
    └── views/
        ├── flight_plan_views.xml
        ├── flight_plan_route_views.xml
        ├── flight_route_waypoint_views.xml
        └── flight_plan_aerodrome_views.xml

Use Cases
=========

- **IFR Operations**: Store instrument flight rules navigation data
- **Route Planning**: Define and reuse common routes
- **Flight Tracking**: Record actual flight paths
- **Regulatory Compliance**: Maintain required flight plan documentation

Technical Details
=================

- **JSON Storage**: Uses flight_json_widget for complex data
- **Integration**: Links with flight_event for phases
- **Waypoint System**: Flexible waypoint and route management
- **Aerodrome Links**: Connects to flight aerodrome records

Support
=======

- **Author**: Apexive Solutions LLC
- **Website**: https://github.com/smartops-aero/smartops-odoo-flight
- **License**: LGPL-3
