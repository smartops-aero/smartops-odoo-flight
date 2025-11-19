=============
Flight Portal
=============

Portal access for sharing flight information with external users via secure access tokens in Odoo 16.

Overview
========

Adds portal functionality to the Flight module, allowing you to share flight information securely with external stakeholders through Odoo's portal system.

Features
========

- **Secure Access Tokens**: Share flights via secure, unique URLs
- **Portal Views**: Dedicated flight views for portal users
- **Access Control**: Fine-grained security rules for portal access
- **External Sharing**: Allow clients, partners, or crew to view flight details

Installation
============

1. Install from Odoo Apps menu
2. Requires: ``flight``, ``portal``, ``web`` modules

Usage
=====

Share Flight Information
------------------------

1. Open a **Flight** record
2. Use the portal sharing features to generate access tokens
3. Share the secure URL with external users
4. Portal users can view flight details without system access

Configure Portal Access
------------------------

1. Set up portal users through **Settings → Users & Companies → Users**
2. Assign portal access rights
3. Users can access shared flights through their portal

Module Structure
================

.. code-block:: text

    flight_portal/
    ├── models/
    │   └── flight_flight.py              # Extends flight with portal features
    ├── security/
    │   ├── ir.model.access.csv           # Access rights for portal users
    │   └── flight_portal_security.xml     # Security rules
    └── views/
        ├── flight_views.xml               # Portal-enabled flight views
        └── flight_portal_templates.xml    # Portal page templates

Use Cases
=========

- **Client Updates**: Share flight status with clients without system access
- **Crew Coordination**: Allow crew members to view their assigned flights
- **Partner Collaboration**: Share operational details with partners securely
- **Charter Services**: Provide flight details to charter clients

Technical Details
=================

- **Portal Integration**: Uses Odoo's standard portal framework
- **Security**: Token-based access with record rules
- **Templates**: QWeb templates for portal interface
- **Extensible**: Easy to customize portal views

Support
=======

- **Author**: Apexive Solutions LLC
- **Website**: https://github.com/smartops-aero/smartops-odoo-flight
- **License**: LGPL-3
