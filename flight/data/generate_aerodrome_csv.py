#!/usr/bin/env python3
import csv

import airportsdata

airports = airportsdata.load()

fieldnames = [
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


with open("flight.aerodrome.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
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
