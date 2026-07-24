#!/usr/bin/env python3
"""
Generate aerodrome and runway CSV data for Odoo import.

Aerodrome data: From airportsdata Python library (~28,000 airports)
Runway data: From OurAirports database (https://davidmegginson.github.io/ourairports-data/)
ICAO country prefixes: derived from the same airportsdata dataset — the ICAO
    location-indicator prefix -> country table (res.country.icao_prefixes).

Usage:
    1. Download runway source data:
       wget https://davidmegginson.github.io/ourairports-data/runways.csv -O ourairports_source_runways.csv

    2. Run this script:
       python3 generate_aerodrome_csv.py

    3. Generated CSVs:
       - flight.aerodrome.csv
       - flight.aerodrome.runway.csv
       - res.country.csv          (loaded on module install/upgrade)

Known Issues:
    1. Deprecated Timezones: The airportsdata library may include deprecated timezone
       names that are not supported by Odoo's pytz selection field. After generating
       the CSV, you may need to replace the following:
         - Europe/Uzhgorod  -> Europe/Kyiv
         - Europe/Zaporozhye -> Europe/Kyiv
       Use: sed -i '' 's/Europe\\/Uzhgorod/Europe\\/Kyiv/g; s/Europe\\/Zaporozhye/Europe\\/Kyiv/g' flight.aerodrome.csv

    2. Odoo Import Limit: Odoo's UI import mechanism may timeout or limit imports to
       ~8,000 records. For the full dataset (~28,000 aerodromes), either:
         - Split the CSV into smaller chunks and import separately
         - Uncomment the CSV in __manifest__.py and upgrade the module
         - Use odoo shell to load records programmatically
"""
import csv
from collections import Counter, defaultdict

import airportsdata

# Conversion factor: feet to meters
FEET_TO_METERS = 0.3048

print("=" * 80)
print("GENERATING AERODROME AND RUNWAY DATA FOR ODOO")
print("=" * 80)

# =============================================================================
# PART 1: GENERATE AERODROMES
# =============================================================================
print("\n📍 PART 1: Generating Aerodromes...")

airports = airportsdata.load()

aerodrome_fieldnames = [
    "id",
    "icao",
    "iata",
    "name",
    "city",
    "municipality",
    "country_id/id",
    "elevation",
    "latitude",
    "longitude",
    "tz",
    "lid",
]

AERODROME_OUTPUT = "flight.aerodrome.csv"

with open(AERODROME_OUTPUT, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(
        csvfile, fieldnames=aerodrome_fieldnames, quoting=csv.QUOTE_ALL
    )
    writer.writeheader()

    for aerodrome in airports.values():
        iso_country = aerodrome.pop("country").lower()
        if iso_country == "gb":
            iso_country = "uk"
        aerodrome["id"] = "aerodrome_" + aerodrome["icao"]
        aerodrome["country_id/id"] = "base." + iso_country
        aerodrome["municipality"] = aerodrome.pop("subd")
        aerodrome["elevation"] = int(aerodrome["elevation"])
        aerodrome["longitude"] = aerodrome.pop("lon")
        aerodrome["latitude"] = aerodrome.pop("lat")

        writer.writerow(aerodrome)

print(f"✅ Generated {len(airports)} aerodromes")
print(f"📄 Output: {AERODROME_OUTPUT}")

# =============================================================================
# PART 2: GENERATE RUNWAYS
# =============================================================================
print("\n🛫 PART 2: Generating Runways...")

# Load valid ICAO codes from aerodromes
valid_icao_codes = set(airports.keys())
print(f"✅ Using {len(valid_icao_codes)} airports from airportsdata")

# Read OurAirports runway data from local file
RUNWAY_SOURCE_FILE = "ourairports_source_runways.csv"
print(f"📖 Reading runway data from {RUNWAY_SOURCE_FILE}...")

try:
    with open(RUNWAY_SOURCE_FILE, encoding="utf-8") as f:
        runway_data = list(csv.DictReader(f))
    print(f"✅ Loaded {len(runway_data)} runways from OurAirports")
except FileNotFoundError:
    print(f"\n❌ ERROR: {RUNWAY_SOURCE_FILE} not found!")
    print("Download it first:")
    print(
        "  wget https://davidmegginson.github.io/ourairports-data/runways.csv "
        f"-O {RUNWAY_SOURCE_FILE}"
    )
    exit(1)

# Output CSV fieldnames for Odoo import (length/width converted to meters)
runway_fieldnames = [
    "id",
    "code",
    "aerodrome_id/id",
    "length",  # will be in meters
    "length_uom_id/id",
    "width",  # will be in meters
    "width_uom_id/id",
]

# Track statistics
matched_count = 0
skipped_count = 0
skipped_missing_icao = 0
skipped_invalid_dimensions = 0
runways_created = set()  # Track unique runways to avoid duplicates

RUNWAY_OUTPUT = "flight.aerodrome.runway.csv"


def is_valid_runway_code(code):
    """Check if runway code will pass Odoo validation"""
    if not code or len(code) < 2 or len(code) > 3:
        return False

    # Special case: "88" is allowed (all runways)
    if code == "88":
        return True

    # Check first two characters are digits 01-36
    try:
        runway_num = int(code[:2])
        if runway_num < 1 or runway_num > 36:
            return False
    except ValueError:
        return False

    # If there's a third character, it must be L/R/C
    if len(code) == 3 and code[2] not in ["L", "R", "C"]:
        return False

    return True


def convert_feet_to_meters(feet_value):
    """Convert feet to meters, return None if invalid"""
    if not feet_value or feet_value.strip() == "":
        return None
    try:
        feet = float(feet_value)
        if feet <= 0:
            return None
        return round(feet * FEET_TO_METERS, 2)
    except (ValueError, TypeError):
        return None


with open(RUNWAY_OUTPUT, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(
        csvfile, fieldnames=runway_fieldnames, quoting=csv.QUOTE_ALL
    )
    writer.writeheader()

    for runway in runway_data:
        # Get airport ICAO code (OurAirports uses 'airport_ident' field)
        icao = runway.get("airport_ident", "").upper()

        if not icao:
            skipped_missing_icao += 1
            continue

        # Only include runways for airports in our aerodrome data
        if icao not in valid_icao_codes:
            skipped_count += 1
            continue

        # Skip closed runways
        if runway.get("closed", "0") == "1":
            skipped_count += 1
            continue

        # Extract runway identifiers (le_ident and he_ident are the two ends)
        # We create TWO separate runway records (one for each direction)
        le_ident = runway.get("le_ident", "")
        he_ident = runway.get("he_ident", "")

        if not le_ident or not he_ident:
            # Skip runways without proper identifiers
            continue

        # Get dimensions (convert feet to meters)
        length_m = convert_feet_to_meters(runway.get("length_ft"))
        width_m = convert_feet_to_meters(runway.get("width_ft"))

        # Skip if both dimensions are missing (no useful data)
        if length_m is None and width_m is None:
            skipped_invalid_dimensions += 1
            continue

        # Create runway records for both directions (they share the same dimensions)
        for runway_code in [le_ident, he_ident]:
            # Validate runway code before creating
            if not is_valid_runway_code(runway_code):
                continue

            # Check for duplicates
            unique_key = f"{icao}_{runway_code}"
            if unique_key in runways_created:
                continue

            runways_created.add(unique_key)

            # Create unique ID for this runway
            runway_id = f"runway_{icao}_{runway_code}"

            # Write runway record
            row = {
                "id": runway_id,
                "code": runway_code,
                "aerodrome_id/id": f"aerodrome_{icao}",
                "length": length_m if length_m else "",
                "length_uom_id/id": "uom.product_uom_meter" if length_m else "",
                "width": width_m if width_m else "",
                "width_uom_id/id": "uom.product_uom_meter" if width_m else "",
            }
            writer.writerow(row)

            matched_count += 1

print("\n✅ Generated runway CSV successfully!")
print(f"   - Runways created: {matched_count}")
print(f"   - Skipped (airport not in airportsdata): {skipped_count}")
print(f"   - Skipped (missing ICAO): {skipped_missing_icao}")
print(f"   - Skipped (no valid dimensions): {skipped_invalid_dimensions}")
print(f"📄 Output: {RUNWAY_OUTPUT}")

# =============================================================================
# PART 3: GENERATE ICAO COUNTRY PREFIXES
# =============================================================================
print("\n🌍 PART 3: Generating ICAO country prefixes...")

# Reload unmutated data (PART 1 pops fields from the aerodrome dicts).
prefix_source = airportsdata.load("ICAO")

# Count airports per (prefix, country) at prefix lengths 1..3.
_prefix_counts = {1: defaultdict(Counter), 2: defaultdict(Counter), 3: defaultdict(Counter)}
for _icao, _rec in prefix_source.items():
    _iso = _rec.get("country")
    if not _iso or not _icao.isalpha() or len(_icao) != 4:
        continue
    for _length in (1, 2, 3):
        _prefix_counts[_length][_icao[:_length]][_iso] += 1


def _clean_country(prefix):
    """Return the country a prefix cleanly belongs to (>=97% of its airports,
    at most 3 stray), else None. Skips non-standard X* codes."""
    counter = _prefix_counts[len(prefix)][prefix]
    dominant, n = counter.most_common(1)[0]
    total = sum(counter.values())
    if n / total >= 0.97 and (total - n) <= 3 and not prefix.startswith("X"):
        return dominant
    return None


# For each airport, take the SHORTEST clean prefix and collect it per country.
# This yields 2-letter prefixes where a country owns them, and a 3-letter split
# for genuinely shared regions (e.g. UAF=Kyrgyzstan vs UAA..=Kazakhstan).
country_prefixes = defaultdict(set)
for _icao, _rec in prefix_source.items():
    _iso = _rec.get("country")
    if not _iso or not _icao.isalpha() or len(_icao) != 4:
        continue
    for _length in (1, 2, 3):
        _dominant = _clean_country(_icao[:_length])
        if _dominant:
            country_prefixes[_dominant].add(_icao[:_length])
            break

PREFIX_OUTPUT = "res.country.csv"
with open(PREFIX_OUTPUT, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
    writer.writerow(["id", "icao_prefixes"])
    for _iso in sorted(country_prefixes):
        _xmlid = "base.uk" if _iso == "GB" else f"base.{_iso.lower()}"
        writer.writerow([_xmlid, " ".join(sorted(country_prefixes[_iso]))])

print(f"✅ Generated {len(country_prefixes)} country prefix rows")
print(f"📄 Output: {PREFIX_OUTPUT}")

print("\n" + "=" * 80)
print("✅ GENERATION COMPLETE!")
print("=" * 80)
print("\nGenerated files:")
print(f"  1. {AERODROME_OUTPUT} ({len(airports)} aerodromes)")
print(f"  2. {RUNWAY_OUTPUT} ({matched_count} runways with dimensions)")
print(f"  3. {PREFIX_OUTPUT} ({len(country_prefixes)} country prefix rows)")
print("\nImport these files in Odoo via Settings → Technical → Database Structure")
