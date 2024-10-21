# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [16.0.1.1.1]

### Added

- New `FlightLockMixin` to handle locking logic for flights and related models.
- Implemented immutability for `FlightFlight` model when locked.

### Changed

- Refactored `FlightFlight`

### Security

- Enhanced data integrity by preventing modifications to locked flights and their related records.
