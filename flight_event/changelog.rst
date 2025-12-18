=========
Changelog
=========

18.0.1.2.0
----------

* Implement 3-column layout for flight form view (Flight Info : Map : Time Summary 1:1:1)
* Add tab-based time summary widget with Actual and Scheduled tabs
* Fix view inheritance to use position="after" instead of position="replace"
* Fix FlightTimeInputCell prop validation (eventCode and timeKind as String)

18.0.1.1.0
----------

* Add Flight Time Summary widget
* Add shared FlightTimeInputCell component
* Add useUserTimezone hook for timezone handling
* Refactor matrix widget to use shared components

18.0.1.0.1
----------

* Initial release for Odoo 18.0
* Flight event time matrix widget
* Event code and phase management
