"""Approximate centroids for major Dubai communities (DLD area names).

These are real, publicly-known coordinates for the principal Dubai communities
present in the dataset. Areas without a confident centroid are intentionally
omitted from the map and surfaced in the ranked table instead, so nothing is
fabricated. Coordinates are approximate community centres, sufficient for a
metric-weighted heat / bubble map.
"""
from __future__ import annotations

# area_name_en -> (lat, lon)
AREA_COORDS = {
    "Business Bay": (25.1857, 55.2630),
    "Burj Khalifa": (25.1972, 55.2744),
    "Marsa Dubai": (25.0805, 55.1403),            # Dubai Marina
    "Palm Jumeirah": (25.1124, 55.1390),
    "Palm Deira": (25.3050, 55.3380),
    "Al Wasl": (25.2200, 55.2550),
    "Al Satwa": (25.2300, 55.2730),
    "Al Jadaf": (25.2230, 55.3300),
    "Al Merkadh": (25.1830, 55.3050),             # MBR City / Meydan
    "Hadaeq Sheikh Mohammed Bin Rashid": (25.1750, 55.2950),
    "Al Thanyah Fifth": (25.0950, 55.1700),       # Jumeirah Lakes Towers
    "Al Thanyah Third": (25.0680, 55.1450),
    "Nadd Hessa": (25.2540, 55.4040),             # Dubai Silicon Oasis
    "Jabal Ali First": (25.0050, 55.1300),
    "Madinat Dubai Almelaheyah": (25.2820, 55.2620),  # Dubai Maritime City
    "Al Barsha South Fourth": (25.0700, 55.2380),
    "Al Barsha South Fifth": (25.0600, 55.2450),
    "Al Barshaa South Third": (25.0780, 55.2300),
    "Al Hebiah Fourth": (25.0300, 55.2400),       # Dubai Sports City / Motor City
    "Al Hebiah Third": (25.0250, 55.2550),
    "Al Hebiah Fifth": (25.0200, 55.2250),
    "Wadi Al Safa 5": (25.0650, 55.2900),
    "Wadi Al Safa 3": (25.0700, 55.3050),
    "Wadi Al Safa 2": (25.0750, 55.3150),
    "Wadi Al Safa 7": (25.0600, 55.2750),
    "Madinat Al Mataar": (24.8950, 55.1650),      # Dubai South
    "Me'Aisem First": (25.0400, 55.1900),         # IMPZ / Dubai Production City
    "Al Khairan First": (25.2050, 55.3450),       # Dubai Creek Harbour
    "Nad Al Shiba First": (25.1650, 55.3400),
    "Warsan Fourth": (25.1650, 55.4250),          # International City
    "Al Warsan First": (25.1700, 55.4000),
    "Madinat Hind 4": (25.0000, 55.3000),
    "Dubai Investment Park Second": (24.9750, 55.1750),
    "Al Yelayiss 2": (25.0100, 55.2700),          # Town Square / Dubailand
    "Al Yufrah 1": (24.9200, 55.3500),
}


def coords_for(area: str):
    return AREA_COORDS.get(area)
