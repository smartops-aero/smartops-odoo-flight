Changelog
=========

18.0.1.1.0 (2026-01-09)
-----------------------

**Features**

* Added ``animate`` option for view-level animation control
* Better separation of concerns between view configuration and data

**Changed**

* Widget now accepts ``animate: true/false`` option in XML options
* View-level animation control overrides data-level animation settings
* Default behavior: animations enabled unless explicitly set to ``false``

**Usage**

.. code-block:: xml

    <!-- Disable animations -->
    <field name="map_data" widget="flight_map_view"
           options="{'animate': false}" />

    <!-- Enable animations (default) -->
    <field name="map_data" widget="flight_map_view"
           options="{'animate': true}" />

18.0.1.0.0 (Initial Release)
-----------------------------

**Features**

* Interactive Leaflet-based map widget
* Route visualization with departure and arrival points
* GSAP-powered smooth path animations
* Custom marker icons and styles
* Automatic bounds fitting
* Support for various coordinate formats
* Mobile-friendly touch gestures
* Real-time map updates on field changes
