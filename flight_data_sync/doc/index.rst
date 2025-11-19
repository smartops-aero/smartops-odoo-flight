================
Flight Data Sync
================

Synchronize flight data from external providers with automated scheduling for Odoo 18.

Overview
========

Provides a pluggable, registry-based architecture for syncing flight data from external sources. Configure multiple providers, set up automated cron schedules, and track sync history with detailed logging.

Features
========

- **Provider Registry**: Extensible architecture for adding custom data providers
- **Automated Scheduling**: Cron-based sync schedules for automatic updates
- **API Credentials**: Secure storage of API endpoints, usernames, and passwords
- **Sync History**: Track synchronization attempts through data registry
- **Run As User**: Execute syncs as specific users for proper access control
- **Manual Sync Wizard**: Trigger on-demand syncs for testing or immediate updates

Installation
============

1. Install from Odoo Apps menu
2. Requires: ``flight``, ``mail``, ``web`` modules

Usage
=====

Configure Data Provider
-----------------------

1. Go to **Flights → Configuration → Data Providers**
2. Create a new provider:
   - Set name and service type
   - Enter API base URL
   - Add credentials (username/password)
   - Optionally set "Run As User"

Set Up Sync Schedule
---------------------

1. Open a provider record
2. Add sync schedules in the **Sync Schedules** tab
3. Cron jobs will automatically execute syncs

Manual Sync
-----------

1. Go to **Flights → Data Sync**
2. Use the sync wizard to trigger immediate synchronization

Module Structure
================

::

    flight_data_sync/
    ├── models/
    │   ├── flight_data_provider.py   # Provider configuration
    │   └── flight_data_registry.py   # Sync history tracking
    ├── wizard/
    │   └── flight_data_sync_wizard.py # Manual sync interface
    └── data/
        └── ir_cron_data.xml          # Cron job definitions

For Developers: Adding Custom Providers
========================================

Extend the system by implementing your own data provider:

1. Override ``_selection_service()`` to add your service type
2. Implement sync logic in your provider class
3. Register methods with the data registry
4. System automatically discovers and uses your provider

The modular design allows adding providers without modifying core code.

Use Cases
=========

- **Flight Tracking Integration**: Sync real-time status from FlightAware, FlightRadar24
- **Weather Data**: Pull aviation weather information for operations
- **Airport Data Sync**: Keep aerodrome info updated from ICAO/national databases
- **ERP Integration**: Sync with external aviation management platforms

Technical Details
=================

- **Architecture**: Registry pattern with pluggable providers
- **Scheduling**: Odoo cron system for automated execution
- **Security**: Company-specific configurations, run-as-user support
- **Extensible**: Add providers through inheritance, no core modifications

Support
=======

- **Author**: Apexive Solutions LLC
- **Website**: https://github.com/smartops-aero/smartops-odoo-flight
- **License**: LGPL-3
