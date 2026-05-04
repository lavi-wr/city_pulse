"""
transport_advisor.py  –  CityPulse Transportation Module
=========================================================
Suggests the best mode of transport (Metro, Bus, Bike) for a given
distance, crowd level, time-of-day, and user preference.

Score model (lower = better):
  Each mode gets a composite score from:
    • cost_score    (₹ per km, normalised 0-1)
    • time_score    (estimated travel time, normalised 0-1)
    • comfort_score (fixed penalty per mode, adjusted for crowd & weather)
  Final = w_cost*cost_score + w_time*time_score + w_comfort*comfort_score

Weights default to balanced (equal thirds) but shift when the caller
passes priority="price" or priority="time".
"""

from __future__ import annotations

# ── Transport mode definitions ────────────────────────────────────────────────

MODES = {
    "Metro": {
        "base_fare":       10,       # ₹  boarding charge
        "fare_per_km":     2.5,      # ₹ / km
        "avg_speed_kmh":   35,       # door-to-door including walk + wait
        "comfort_base":    0.2,      # 0 = best, 1 = worst  (comfort penalty)
        "crowd_penalty":   0.15,     # added when crowd == High
        "peak_penalty":    0.10,     # added during peak hours (17-19)
        "available_after": 6,        # first service hour
        "available_until": 23,       # last service hour
        "rain_friendly":   True,
        "emoji":           "🚇",
    },
    "Bus": {
        "base_fare":       10,
        "fare_per_km":     1.5,
        "avg_speed_kmh":   18,
        "comfort_base":    0.35,
        "crowd_penalty":   0.20,
        "peak_penalty":    0.15,
        "available_after": 5,
        "available_until": 23,
        "rain_friendly":   True,
        "emoji":           "🚌",
    },
    "Bike": {
        "base_fare":       0,
        "fare_per_km":     0,        # rental ~₹2/min, approximated below
        "avg_speed_kmh":   15,
        "comfort_base":    0.25,
        "crowd_penalty":   0.0,      # bikes dodge traffic
        "peak_penalty":    0.05,
        "available_after": 6,
        "available_until": 22,
        "rain_friendly":   False,
        "emoji":           "🚲",
        "rental_per_min":  2,        # ₹ / minute (e.g. Yulu / Bounce)
    },
}

PEAK_HOURS = {17, 18, 19}


# ── Cost helpers ──────────────────────────────────────────────────────────────

def estimate_cost(mode_name: str, distance_km: float) -> float:
    m = MODES[mode_name]
    if mode_name == "Bike":
        minutes = (distance_km / m["avg_speed_kmh"]) * 60
        return round(m["rental_per_min"] * minutes, 1)
    return round(m["base_fare"] + m["fare_per_km"] * distance_km, 1)


def estimate_time(mode_name: str, distance_km: float) -> float:
    """Returns travel time in minutes."""
    speed = MODES[mode_name]["avg_speed_kmh"]
    return round((distance_km / speed) * 60, 1)


# ── Availability check ────────────────────────────────────────────────────────

def is_available(mode_name: str, hour: int, raining: bool = False) -> tuple[bool, str]:
    m = MODES[mode_name]
    if hour < m["available_after"] or hour >= m["available_until"]:
        return False, f"Not running at {hour}:00"
    if raining and not m["rain_friendly"]:
        return False, "Not suitable in rain"
    return True, ""


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_mode(
    mode_name: str,
    distance_km: float,
    crowd: str,
    hour: int,
    weights: dict,
) -> float:
    m = MODES[mode_name]

    cost = estimate_cost(mode_name, distance_km)
    time = estimate_time(mode_name, distance_km)

    # Normalise cost (₹0 → ₹200 scale)
    cost_score = min(cost / 200.0, 1.0)

    # Normalise time (0 → 90 min scale)
    time_score = min(time / 90.0, 1.0)

    # Comfort
    comfort = m["comfort_base"]
    if crowd == "High":
        comfort += m["crowd_penalty"]
    if hour in PEAK_HOURS:
        comfort += m["peak_penalty"]
    comfort_score = min(comfort, 1.0)

    total = (
        weights["cost"]    * cost_score
        + weights["time"]  * time_score
        + weights["comfort"] * comfort_score
    )
    return round(total, 4)


def _get_weights(priority: str) -> dict:
    if priority == "price":
        return {"cost": 0.60, "time": 0.20, "comfort": 0.20}
    if priority == "time":
        return {"cost": 0.20, "time": 0.60, "comfort": 0.20}
    # balanced (default)
    return {"cost": 0.34, "time": 0.33, "comfort": 0.33}


# ── Public API ────────────────────────────────────────────────────────────────

def recommend_transport(
    distance_km: float,
    crowd: str       = "Medium",
    hour: int        = 12,
    priority: str    = "balanced",
    raining: bool    = False,
) -> dict:
    """
    Returns a dict with:
      - ranked   : list of dicts (mode, cost, time_min, score, available, reason)
      - best     : the top available mode dict
      - summary  : human-readable string
    """
    weights = _get_weights(priority)
    results = []

    for mode_name in MODES:
        available, unavail_reason = is_available(mode_name, hour, raining)
        cost     = estimate_cost(mode_name, distance_km)
        time_min = estimate_time(mode_name, distance_km)

        if available:
            score = _score_mode(mode_name, distance_km, crowd, hour, weights)
        else:
            score = 99.0   # push unavailable to bottom

        results.append({
            "mode":       mode_name,
            "emoji":      MODES[mode_name]["emoji"],
            "cost":       cost,
            "time_min":   time_min,
            "score":      score,
            "available":  available,
            "reason":     unavail_reason,
        })

    results.sort(key=lambda x: x["score"])

    available_modes = [r for r in results if r["available"]]
    best = available_modes[0] if available_modes else None

    return {
        "ranked": results,
        "best":   best,
        "priority": priority,
    }


# ── Pretty printer ────────────────────────────────────────────────────────────

def print_transport_advice(distance_km: float, result: dict) -> None:
    ranked   = result["ranked"]
    best     = result["best"]
    priority = result["priority"]

    priority_label = {
        "price":    "cheapest",
        "time":     "fastest",
        "balanced": "balanced (cost + time)",
    }.get(priority, priority)

    print("\n=== TRANSPORT ADVISORY ===")
    print(f"   📏 Distance  : ~{distance_km} km")
    print(f"   🎯 Priority  : {priority_label}")
    print()

    for r in ranked:
        mode  = r["mode"]
        emoji = r["emoji"]
        if r["available"]:
            tag = "⭐ BEST" if r == best else "     "
            print(f"  {tag}  {emoji} {mode:<6}  ₹{r['cost']:<6.0f}  ~{r['time_min']:.0f} min")
        else:
            print(f"         {emoji} {mode:<6}  ❌ {r['reason']}")

    if best:
        b = best
        print(f"\n👉 Recommended: {b['emoji']} {b['mode']}")
        print(f"   Cost  : ₹{b['cost']:.0f}")
        print(f"   Time  : ~{b['time_min']:.0f} minutes")
    else:
        print("\n⚠️  No transport modes available right now.")