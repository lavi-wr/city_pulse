"""
distance_api.py  –  OpenRouteService (OpenStreetMap) distance + geocoding
-------------------------------------------------------------------------
Requires:
    pip install requests

Free ORS API key: https://openrouteservice.org/dev/#/signup
    export ORS_API_KEY="your_key_here"
"""

import os
import requests

ORS_API_KEY = os.getenv("ORS_API_KEY", "")

PROFILE_MAP = {
    "driving":  "driving-car",
    "walking":  "foot-walking",
    "cycling":  "cycling-regular",
    "bike":     "cycling-regular",
    "auto":     "driving-car",
}

GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
MATRIX_URL  = "https://api.openrouteservice.org/v2/matrix/{profile}"


def _geocode(address: str) -> tuple[float, float] | None:
    if not ORS_API_KEY:
        return None
    try:
        r = requests.get(
            GEOCODE_URL,
            params={"api_key": ORS_API_KEY, "text": address, "size": 1},
            timeout=8,
        )
        r.raise_for_status()
        features = r.json().get("features", [])
        if not features:
            return None
        return tuple(features[0]["geometry"]["coordinates"])  # (lon, lat)
    except Exception:
        return None


def _matrix(origin_lonlat, dest_lonlat, profile="driving-car"):
    if not ORS_API_KEY:
        return None, None
    try:
        r = requests.post(
            MATRIX_URL.format(profile=profile),
            json={
                "locations": [list(origin_lonlat), list(dest_lonlat)],
                "metrics":   ["distance", "duration"],
                "units":     "km",
            },
            headers={
                "Authorization": ORS_API_KEY,
                "Content-Type":  "application/json",
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        return round(data["distances"][0][1], 2), round(data["durations"][0][1] / 60, 1)
    except Exception:
        return None, None


def get_distance_km(origin: str, destination: str, mode: str = "driving") -> float | None:
    profile = PROFILE_MAP.get(mode, "driving-car")
    o = _geocode(origin)
    d = _geocode(destination)
    if not o or not d:
        return None
    dist_km, _ = _matrix(o, d, profile)
    return dist_km


def get_distance_and_duration(origin: str, destination: str, mode: str = "driving") -> dict:
    profile = PROFILE_MAP.get(mode, "driving-car")
    o = _geocode(origin)
    d = _geocode(destination)
    base = {"distance_km": None, "duration_min": None,
            "mode": mode, "profile": profile,
            "origin": origin, "destination": destination}
    if not o or not d:
        return base
    dist_km, dur_min = _matrix(o, d, profile)
    return {**base, "distance_km": dist_km, "duration_min": dur_min}


def get_all_modes(origin: str, destination: str) -> dict[str, dict]:
    return {mode: get_distance_and_duration(origin, destination, mode)
            for mode in ("driving", "walking", "cycling")}


# ── IP geolocation with 3 fallback providers ──────────────────────────────────

def _fmt(city, region, country) -> str | None:
    parts = [p for p in [city, region, country] if p]
    return ", ".join(parts) if parts else None


def _try_ipwho() -> str | None:
    """ipwho.is — free, no API key needed."""
    try:
        data = requests.get("https://ipwho.is/", timeout=5).json()
        if not data.get("success"):
            return None
        return _fmt(data.get("city"), data.get("region"), data.get("country"))
    except Exception:
        return None


def _try_ip_api() -> str | None:
    """ip-api.com — free, no API key needed."""
    try:
        data = requests.get(
            "http://ip-api.com/json/?fields=status,city,regionName,country",
            timeout=5,
        ).json()
        if data.get("status") != "success":
            return None
        return _fmt(data.get("city"), data.get("regionName"), data.get("country"))
    except Exception:
        return None


def _try_ipinfo() -> str | None:
    """ipinfo.io — free tier, no key for basic fields."""
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        return _fmt(data.get("city"), data.get("region"), data.get("country"))
    except Exception:
        return None


def get_user_location_address() -> str | None:
    """
    Tries 3 free IP-geolocation services in order.
    Returns a city/region/country string, or None if all fail.
    """
    for fn in (_try_ipwho, _try_ip_api, _try_ipinfo):
        result = fn()
        if result:
            return result
    return None