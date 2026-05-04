"""
distance_api.py  –  CityPulse Distance Module
==============================================
Fetches real-world driving/transit distance between the user's current
location and a destination using the Google Maps Distance Matrix API.

Usage:
    from distance_api import get_distance_km

    km = get_distance_km(
        origin="Connaught Place, New Delhi",
        destination="Select Citywalk, Saket, New Delhi",
        mode="driving",          # "driving" | "transit" | "walking" | "bicycling"
    )

Requirements:
    pip install requests

Environment variable (set once):
    GOOGLE_MAPS_API_KEY=your_key_here

Get a free key (with generous daily quota) at:
    https://console.cloud.google.com/
    Enable → "Distance Matrix API"
"""

from __future__ import annotations

import os
import requests

# ── Config ────────────────────────────────────────────────────────────────────

DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"

# Read key from environment so it's never hard-coded in source
_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")


# ── Public API ────────────────────────────────────────────────────────────────

def get_distance_km(
    origin: str,
    destination: str,
    mode: str = "driving",
) -> float | None:
    """
    Returns the road/transit distance in kilometres between origin and
    destination, or None if the API call fails.

    Parameters
    ----------
    origin      : free-text address or "lat,lng"  e.g. "28.6139,77.2090"
    destination : free-text address or "lat,lng"
    mode        : "driving" | "transit" | "walking" | "bicycling"
    """
    if not _API_KEY:
        print("⚠️  GOOGLE_MAPS_API_KEY not set. Falling back to manual entry.")
        return None

    params = {
        "origins":      origin,
        "destinations": destination,
        "mode":         mode,
        "key":          _API_KEY,
        "units":        "metric",
        "language":     "en",
    }

    try:
        resp = requests.get(DISTANCE_MATRIX_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status", "")
        if status != "OK":
            print(f"⚠️  Distance Matrix API error: {status}")
            return None

        element = data["rows"][0]["elements"][0]
        el_status = element.get("status", "")
        if el_status != "OK":
            print(f"⚠️  Route not found: {el_status}")
            return None

        metres = element["distance"]["value"]
        return round(metres / 1000.0, 2)

    except requests.exceptions.Timeout:
        print("⚠️  Distance API timed out.")
        return None
    except Exception as exc:
        print(f"⚠️  Distance API error: {exc}")
        return None


def get_distance_with_duration(
    origin: str,
    destination: str,
    mode: str = "driving",
) -> dict | None:
    """
    Like get_distance_km() but returns a dict with both distance and
    estimated travel duration:

        {
            "distance_km": 7.3,
            "duration_min": 22,
            "distance_text": "7.3 km",
            "duration_text": "22 mins",
        }
    """
    if not _API_KEY:
        print("⚠️  GOOGLE_MAPS_API_KEY not set.")
        return None

    params = {
        "origins":      origin,
        "destinations": destination,
        "mode":         mode,
        "key":          _API_KEY,
        "units":        "metric",
        "language":     "en",
    }

    try:
        resp = requests.get(DISTANCE_MATRIX_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK":
            return None

        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            return None

        return {
            "distance_km":    round(element["distance"]["value"] / 1000.0, 2),
            "duration_min":   round(element["duration"]["value"] / 60.0, 1),
            "distance_text":  element["distance"]["text"],
            "duration_text":  element["duration"]["text"],
        }

    except Exception as exc:
        print(f"⚠️  Distance API error: {exc}")
        return None


# ── Geolocation helper ────────────────────────────────────────────────────────

def get_user_location_address() -> str | None:
    """
    Attempts to get the user's approximate address via the Google
    Geolocation API (requires 'Geolocation API' enabled in your project).

    Returns a free-text address string suitable for use as `origin`,
    or None on failure.

    NOTE: For a CLI app the simplest alternative is to ask the user once
    and cache the result — see main.py for how that's done.
    """
    if not _API_KEY:
        return None

    geo_url = "https://www.googleapis.com/geolocation/v1/geolocate"
    try:
        resp = requests.post(
            geo_url,
            params={"key": _API_KEY},
            json={"considerIp": True},
            timeout=6,
        )
        resp.raise_for_status()
        loc = resp.json().get("location", {})
        lat, lng = loc.get("lat"), loc.get("lng")
        if lat and lng:
            return f"{lat},{lng}"
    except Exception:
        pass
    return None