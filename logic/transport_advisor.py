"""
transport_advisor.py  –  ORS-powered transport recommendations
--------------------------------------------------------------
Uses real driving / walking / cycling travel times from OpenRouteService
instead of rule-of-thumb estimates.
"""

from __future__ import annotations


# ── Cost estimates (INR, approximate Delhi rates) ─────────────────────────────

def _auto_cost(km: float) -> tuple[float, float]:
    """Returns (min_inr, max_inr) for an auto-rickshaw trip."""
    base, per_km = 25, 10
    total = base + km * per_km
    return round(total * 0.9), round(total * 1.2)      # haggle range


def _cab_cost(km: float, hour: int) -> tuple[float, float]:
    """Ola/Uber estimate with surge for rush hours."""
    base, per_km = 50, 12
    surge = 1.4 if hour in range(17, 21) else 1.0
    mini  = (base + km * per_km) * surge
    return round(mini), round(mini * 1.3)              # Mini → Prime range


def _metro_cost(km: float) -> int:
    """Delhi Metro flat-slab fare (approx)."""
    if km <= 2:   return 10
    if km <= 5:   return 20
    if km <= 12:  return 30
    if km <= 21:  return 40
    if km <= 32:  return 50
    return 60


# ── Main recommendation logic ─────────────────────────────────────────────────

def recommend_transport(
    distance_km: float,
    crowd: str,
    hour: int,
    priority: str = "balanced",
    raining: bool = False,
    ors_modes: dict | None = None,   # from distance_api.get_all_modes()
) -> dict:
    """
    Builds a ranked list of transport options.

    Parameters
    ----------
    distance_km  : road distance (driving) in km
    crowd        : "Low" | "Medium" | "High"
    hour         : departure hour (0-23)
    priority     : "balanced" | "price" | "time"
    raining      : True if it's raining
    ors_modes    : dict returned by distance_api.get_all_modes()
                   {mode: {distance_km, duration_min, ...}}
                   If None, durations are estimated from distance.

    Returns
    -------
    dict with keys: options (list of option dicts), best (str)
    """

    # ── Extract real durations where available ────────────────────────────────
    def dur(mode: str, fallback_min: float) -> float:
        if ors_modes and mode in ors_modes:
            val = ors_modes[mode].get("duration_min")
            if val is not None:
                return val
        return fallback_min

    drive_min   = dur("driving",  distance_km * 3)    # ~20 km/h city average
    walk_min    = dur("walking",  distance_km * 13)   # ~4.5 km/h
    cycle_min   = dur("cycling",  distance_km * 5)    # ~12 km/h

    rush_hour   = hour in range(17, 21) or hour in range(8, 11)
    metro_ok    = distance_km >= 2      # metro is practical above 2 km
    walk_ok     = distance_km <= 1.5 and not raining
    cycle_ok    = distance_km <= 8  and not raining and crowd != "High"

    options = []

    # ── Walking ───────────────────────────────────────────────────────────────
    if walk_ok:
        options.append({
            "mode":    "🚶 Walk",
            "time":    round(walk_min),
            "cost":    "₹0",
            "eco":     True,
            "summary": "Free & healthy for short distances",
            "score":   {"balanced": 80, "price": 100, "time": 20}[priority],
        })

    # ── Metro ─────────────────────────────────────────────────────────────────
    if metro_ok:
        fare   = _metro_cost(distance_km)
        # Rough metro time: 5 min walk + 3 min wait + line time
        m_time = 5 + 3 + round(distance_km * 2.5)
        note   = "Avoid rush hours (8-10 AM, 5-8 PM)" if rush_hour else "Good option right now"
        options.append({
            "mode":    "🚇 Metro",
            "time":    m_time,
            "cost":    f"₹{fare}",
            "eco":     True,
            "summary": note,
            "score":   {"balanced": 85, "price": 90, "time": 60}[priority],
        })

    # ── Cycling ───────────────────────────────────────────────────────────────
    if cycle_ok:
        options.append({
            "mode":    "🚲 Cycle / E-scooter",
            "time":    round(cycle_min),
            "cost":    "₹10–30",
            "eco":     True,
            "summary": "Eco-friendly; check Yulu/Bounce availability",
            "score":   {"balanced": 75, "price": 95, "time": 50}[priority],
        })

    # ── Auto-rickshaw ─────────────────────────────────────────────────────────
    if distance_km <= 15:
        lo, hi = _auto_cost(distance_km)
        options.append({
            "mode":    "🛺 Auto-rickshaw",
            "time":    round(drive_min * 1.1),
            "cost":    f"₹{lo}–{hi}",
            "eco":     False,
            "summary": "Haggle or use Ola Auto / Rapido",
            "score":   {"balanced": 70, "price": 75, "time": 55}[priority],
        })

    # ── Cab (Ola/Uber) ────────────────────────────────────────────────────────
    lo, hi = _cab_cost(distance_km, hour)
    cab_note = "Surge pricing likely now" if rush_hour else "Good time for a cab"
    options.append({
        "mode":    "🚖 Cab (Ola/Uber)",
        "time":    round(drive_min),
        "cost":    f"₹{lo}–{hi}",
        "eco":     False,
        "summary": cab_note,
        "score":   {"balanced": 60, "price": 30, "time": 90}[priority],
    })

    # ── Bus ───────────────────────────────────────────────────────────────────
    if distance_km >= 3:
        bus_time = round(drive_min * 1.5)
        options.append({
            "mode":    "🚌 DTC Bus",
            "time":    bus_time,
            "cost":    "₹10–25",
            "eco":     True,
            "summary": "Very cheap; use Google Maps for routes",
            "score":   {"balanced": 65, "price": 98, "time": 10}[priority],
        })

    # ── Sort by priority score (desc) ─────────────────────────────────────────
    options.sort(key=lambda x: x["score"], reverse=True)

    best = options[0]["mode"] if options else "Unknown"
    return {"options": options, "best": best}


# ── Display helper ────────────────────────────────────────────────────────────

def print_transport_advice(distance_km: float, result: dict, ors_modes: dict | None = None) -> None:
    print(f"\n🚦 Transport Options  (distance: {distance_km} km)")

    if ors_modes:
        print("   📡 Travel times via OpenRouteService (OpenStreetMap)")

    print(f"   ⭐ Best pick: {result['best']}\n")

    for opt in result["options"]:
        eco = " 🌿" if opt["eco"] else ""
        print(f"   {opt['mode']}{eco}")
        print(f"      ⏱  ~{opt['time']} min   💰 {opt['cost']}")
        print(f"      ℹ️  {opt['summary']}")
        print()