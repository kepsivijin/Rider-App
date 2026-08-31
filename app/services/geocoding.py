import re
from typing import Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

COORD_PATTERN = re.compile(r"^-?\d+\.\d+,\s*-?\d+\.\d+$")

# Only snap to a preset village when the tap is very close to its center
PRESET_SNAP_KM = 0.4

KNOWN_LOCATIONS = {
    "Eramanthurai": (8.2875, 77.105),
    "Marthandanthurai": (8.2875, 77.105),
    "Vallavilai": (8.2815, 77.1143),
    "Nithiravilai": (8.2739, 77.1436),
    "Marthandam": (8.3076, 77.2218),
    "Kollancode": (8.289, 77.108),
    "Poothurai (Pottur)": (8.264, 77.138),
    "St Thomas Forane Church, Thoothoor": (8.261, 77.1431),
}

_geocoder = Nominatim(user_agent="kanyakumari-rideshare/1.0")


def _nearest_preset(lat: float, lng: float) -> Optional[str]:
    from app.services.ride_matching import haversine_distance

    best_name = None
    best_dist = PRESET_SNAP_KM
    for name, (loc_lat, loc_lng) in KNOWN_LOCATIONS.items():
        dist = haversine_distance(lat, lng, loc_lat, loc_lng)
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name


def _format_nominatim_address(raw: dict) -> Optional[str]:
    address = raw.get("address", {})
    road = (
        address.get("road")
        or address.get("street")
        or address.get("pedestrian")
        or address.get("footway")
        or address.get("path")
        or address.get("residential")
    )
    area = (
        address.get("neighbourhood")
        or address.get("suburb")
        or address.get("hamlet")
        or address.get("locality")
    )
    village = address.get("village") or address.get("town") or address.get("city")
    district = address.get("state_district") or address.get("county")

    parts = []
    if road:
        parts.append(road)
    if area and area not in parts:
        parts.append(area)
    if village and village not in parts:
        parts.append(village)
    if district and district not in parts and len(parts) < 3:
        parts.append(district)

    if parts:
        return ", ".join(parts[:4])

    display = raw.get("display_name") or ""
    if display:
        return ", ".join(display.split(",")[:3]).strip()
    return None


def needs_geocoding(address: str) -> bool:
    if not address or address.strip() in ("Current Location", "Unknown Location"):
        return True
    return bool(COORD_PATTERN.match(address.strip()))


def reverse_geocode(lat: float, lng: float) -> str:
    # Prefer real street names from OpenStreetMap first
    try:
        location = _geocoder.reverse(f"{lat}, {lng}", language="en", timeout=5)
        if location and location.raw:
            formatted = _format_nominatim_address(location.raw)
            if formatted:
                return formatted
    except (GeocoderTimedOut, GeocoderServiceError, Exception):
        pass

    # Only snap to a preset village when very close to its center
    preset = _nearest_preset(lat, lng)
    if preset:
        return preset

    return f"Near {lat:.4f}, {lng:.4f}"


def resolve_address(address: str, lat: float, lng: float) -> str:
    if needs_geocoding(address):
        return reverse_geocode(lat, lng)
    return address
