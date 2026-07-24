#!/usr/bin/env python3
"""
Generate aerodrome and runway CSV data for Odoo import.

Aerodrome data: From airportsdata Python library (~28,000 airports)
Runway data: From OurAirports database (https://davidmegginson.github.io/ourairports-data/)
ICAO country prefixes: res.country.csv is the authoritative table (from the
    Astana Air DST/GMT-deviations reference), maintained by hand. PART 3 only
    cross-checks it against airportsdata and reports differences.

Usage:
    1. Download runway source data:
       wget https://davidmegginson.github.io/ourairports-data/runways.csv -O ourairports_source_runways.csv

    2. Run this script:
       python3 generate_aerodrome_csv.py

    3. Generated CSVs:
       - flight.aerodrome.csv
       - flight.aerodrome.runway.csv
       (res.country.csv is maintained by hand; PART 3 only cross-checks it)

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
# PART 3: CROSS-CHECK ICAO COUNTRY PREFIXES
# =============================================================================
# ``res.country.csv`` is the authoritative ICAO location-indicator prefix ->
# country table (from the Astana Air DST/GMT-deviations reference), maintained
# by hand. This part does NOT regenerate it — it re-derives a candidate from
# airportsdata and reports where the committed table differs, so a maintainer
# can spot new/changed prefixes. Nothing is written.
print("\n🌍 PART 3: Cross-checking res.country.csv against airportsdata...")

# Reload unmutated data (PART 1 pops fields from the aerodrome dicts).
prefix_source = airportsdata.load("ICAO")

# Airportsdata: dominant country per 2-letter prefix (matches the official
# table's granularity).
_pref_counts = defaultdict(Counter)
for _icao, _rec in prefix_source.items():
    _iso = _rec.get("country")
    if not _iso or not _icao.isalpha() or len(_icao) != 4:
        continue
    _pref_counts[_icao[:2]][_iso] += 1
derived = {
    _pref: _counter.most_common(1)[0][0]
    for _pref, _counter in _pref_counts.items()
    if _counter.most_common(1)[0][1] / sum(_counter.values()) >= 0.90
}

# Committed official table: prefix -> ISO
official = {}
try:
    with open("res.country.csv", encoding="utf-8") as f:
        for _row in csv.DictReader(f):
            _iso = _row["id"].split(".")[1].upper()
            _iso = "GB" if _iso == "UK" else _iso
            for _p in _row["icao_prefixes"].split():
                official[_p] = _iso
except FileNotFoundError:
    print("⚠️  res.country.csv not found — skipping cross-check.")
    official = None

if official is not None:
    _diffs = sorted(
        (p, official[p], derived[p])
        for p in official
        if p in derived and official[p] != derived[p]
    )
    _new = sorted(p for p in derived if p not in official and len(p) == 2)
    print(f"✅ committed prefixes: {len(official)}   airportsdata 2-letter: {len(derived)}")
    print(f"   disagreements: {len(_diffs)}   airportsdata-only 2-letter: {len(_new)}")
    for _p, _o, _d in _diffs[:40]:
        print(f"     {_p}: committed={_o}  airportsdata={_d}")
    if _new:
        print(f"   airportsdata-only prefixes: {' '.join(_new[:40])}")

print("\n" + "=" * 80)
print("✅ GENERATION COMPLETE!")
print("=" * 80)
print("\nGenerated files:")
print(f"  1. {AERODROME_OUTPUT} ({len(airports)} aerodromes)")
print(f"  2. {RUNWAY_OUTPUT} ({matched_count} runways with dimensions)")
print("\nImport these files in Odoo via Settings → Technical → Database Structure")
