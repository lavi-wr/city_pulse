import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "api"))
sys.path.insert(0, os.path.join(ROOT, "logic"))

from api.weather_api import get_weather
from api.aqi_api import get_aqi
from api.distance_api import get_distance_km, get_user_location_address   # ← NEW
from logic.time_slot_logic import recommend_time
from logic.advisory_engine import final_advice
from logic.transport_advisor import recommend_transport, print_transport_advice

import pandas as pd
from datetime import datetime

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# ── City suffix appended to every place name for better geocoding ─────────────
CITY_SUFFIX = ", New Delhi, India"


def divider(char="─", width=44):
    print(char * width)

def aqi_label(aqi):
    if   aqi <= 50:  return "Good 🟢"
    elif aqi <= 100: return "Moderate 🟡"
    elif aqi <= 200: return "Unhealthy 🟠"
    else:            return "Very Unhealthy 🔴"

def calculate_risk(aqi, temp, crowd):
    if crowd == "Low":
        if aqi > 150 and temp > 35:
            return "Moderate"
        return "Low"
    if crowd == "Medium":
        if aqi > 200 or temp > 40:
            return "High"
        return "Moderate"
    if aqi > 150 or temp > 35:
        return "High"
    return "Moderate"

def show_places(df):
    print("\n📍 Available places:")
    for i, row in df.iterrows():
        metro_info = ""
        if "nearest_metro" in df.columns and pd.notna(row.get("nearest_metro")):
            metro_info = f"  🚇 {row['nearest_metro']} ({row.get('metro_line','')})"
        print(f"   {i+1:>2}. {row['place_name']}{metro_info}")

def ask_time_preference(now_hour, now_day):
    print("\n⏰ When are you planning to go?")
    print("   1. Right now")
    print("   2. Choose a specific time / day")
    while True:
        choice = input("\n   Enter choice [1/2]: ").strip()
        if choice == "1":
            return None, None
        if choice == "2":
            hour    = _ask_hour(now_hour)
            day_str = _ask_day(now_day)
            return hour, day_str
        print("   ❌ Please enter 1 or 2.")

def _ask_hour(default):
    raw = input(f"\n   Enter hour (0–23)  [press Enter for {default}:00]: ").strip()
    if raw == "":
        return default
    raw = raw.split(":")[0].strip()
    try:
        h = int(raw)
        if 0 <= h <= 23:
            return h
        print(f"   ⚠️  {h} is out of range (0-23). Using {default}:00.")
        return default
    except ValueError:
        print(f"   ⚠️  Could not read '{raw}'. Using {default}:00.")
        return default

def _ask_day(default):
    print(f"\n   Choose a day:")
    for i, d in enumerate(DAYS, 1):
        marker = "  ◀ today" if d == default else ""
        print(f"     {i}. {d}{marker}")
    raw = input(f"   Enter number or name [press Enter for {default}]: ").strip()
    if raw == "":
        return default
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(DAYS):
            return DAYS[idx]
        print(f"   ⚠️  Invalid number. Using {default}.")
        return default
    matched = [d for d in DAYS if d.lower().startswith(raw.lower())]
    if len(matched) == 1:
        return matched[0]
    print(f"   ⚠️  Not recognised. Using {default}.")
    return default


# ── Location helpers ──────────────────────────────────────────────────────────

def get_user_origin(cached_origin: str | None) -> str:
    """
    Returns the user's origin address.
    Uses cached value if already set; otherwise tries IP-geolocation,
    then falls back to asking the user.
    """
    if cached_origin:
        return cached_origin

    print("\n📍 Detecting your location via IP…", end=" ", flush=True)
    auto = get_user_location_address()
    if auto:
        print("✅")
        return auto

    print("❌ (could not auto-detect)")
    return _ask_origin_manually()

def _ask_origin_manually() -> str:
    print("\n   Enter your starting location:")
    print("   (e.g.  Laxmi Nagar, Delhi  or  28.6315,77.2167)")
    raw = input("   → ").strip()
    return raw if raw else "New Delhi, India"


# ── Transport helpers ─────────────────────────────────────────────────────────

def fetch_distance(origin: str, place_name: str) -> float | None:
    """
    Calls the Distance Matrix API and returns km, or None on failure.
    Appends CITY_SUFFIX to the place name for cleaner geocoding.
    """
    destination = place_name + CITY_SUFFIX
    print(f"\n🗺️  Fetching distance: {origin}  →  {place_name}…", end=" ", flush=True)
    km = get_distance_km(origin, destination, mode="driving")
    if km is not None:
        print(f"✅  {km} km")
    else:
        print("❌")
    return km

def ask_transport_preference(
    auto_distance_km: float | None,
) -> tuple[float | None, str]:
    """
    Asks if the user wants transport suggestions.
    If auto_distance_km is available it is shown for confirmation;
    otherwise falls back to manual entry.
    """
    print("\n🚦 Would you like transport suggestions?")
    print("   1. Yes")
    print("   2. No")
    while True:
        choice = input("\n   Enter choice [1/2]: ").strip()
        if choice == "2":
            return None, "balanced"
        if choice == "1":
            distance = _confirm_or_override_distance(auto_distance_km)
            priority = _ask_priority()
            return distance, priority
        print("   ❌ Please enter 1 or 2.")

def _confirm_or_override_distance(auto_km: float | None) -> float:
    if auto_km is not None:
        print(f"\n   📏 Detected distance : {auto_km} km")
        print("   1. Use this distance")
        print("   2. Enter manually")
        while True:
            c = input("\n   Enter choice [1/2]: ").strip()
            if c == "1":
                return auto_km
            if c == "2":
                return _ask_distance()
            print("   ❌ Please enter 1 or 2.")
    return _ask_distance()

def _ask_distance() -> float:
    while True:
        raw = input("\n   Approx. distance from your location (km): ").strip()
        try:
            d = float(raw)
            if d > 0:
                return d
            print("   ⚠️  Distance must be greater than 0.")
        except ValueError:
            print("   ⚠️  Please enter a number (e.g. 5 or 12.5).")

def _ask_priority() -> str:
    print("\n   What matters more to you?")
    print("   1. Balanced  (cost + time equally)")
    print("   2. Price     (cheapest option)")
    print("   3. Time      (fastest option)")
    while True:
        choice = input("\n   Enter choice [1/2/3]: ").strip()
        if choice == "1": return "balanced"
        if choice == "2": return "price"
        if choice == "3": return "time"
        print("   ❌ Please enter 1, 2, or 3.")

def is_raining(aqi: int, temp: float) -> bool:
    """Simple placeholder — replace with weather['is_raining'] if available."""
    return False


# ── Metro display helper ──────────────────────────────────────────────────────

def show_metro_info(place: pd.Series) -> None:
    """Prints the nearest metro station for the selected place."""
    metro = place.get("nearest_metro", "")
    line  = place.get("metro_line", "")
    if metro and str(metro).strip().lower() not in ("", "unknown", "nan"):
        print(f"   🚇 Nearest Metro  : {metro}  ({line})")
    else:
        print("   🚇 Nearest Metro  : Not available")


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    divider("═")
    print("         CITYPULSE — Outing Advisor")
    divider("═")

    print("\n⏳ Fetching live conditions…")
    weather  = get_weather()
    aqi      = get_aqi()
    temp     = weather["temperature"]

    now      = datetime.now()
    now_hour = now.hour
    now_day  = now.strftime("%A")

    print(f"\n📅 {now_day}  🕐 {now.strftime('%H:%M')}")
    print(f"🌡️  Temperature : {temp}°C")
    print(f"💨 AQI         : {aqi}  ({aqi_label(aqi)})")

    places_path = os.path.join(ROOT, "data", "places.csv")
    try:
        df = pd.read_csv(places_path)
    except FileNotFoundError:
        print(f"\n❌ places.csv not found at: {places_path}")
        return

    show_places(df)

    # ── Ask for user's origin once; reuse across all searches ────────────────
    user_origin: str | None = None

    while True:
        print()
        divider()
        place_name = input("Enter place name (or 'exit'): ").strip()

        if place_name.lower() == "exit":
            print("\n👋 Exiting CityPulse. Have a great day!")
            break

        match = df[df["place_name"].str.lower() == place_name.lower()]
        if match.empty:
            print(f"❌ '{place_name}' not found. Check the list above.")
            continue

        place = match.iloc[0]

        divider("─")
        print(f"📍 {place['place_name']}")
        print(f"   Category   : {place['category']}")
        print(f"   Popularity : {place['popularity']}")
        print(f"   Area type  : {place['area_type']}")
        print(f"   Hours      : {int(place['open_hour']):02d}:00 – {int(place['close_hour']):02d}:00")
        show_metro_info(place)          # ← NEW: metro station line

        custom_hour, custom_day = ask_time_preference(now_hour, now_day)

        display_hour = custom_hour if custom_hour is not None else now_hour
        display_day  = custom_day  if custom_day  is not None else now_day
        is_custom    = custom_hour is not None or custom_day != now_day

        print()
        divider("·")
        label = f"{display_day} at {display_hour}:00"
        print(f"   📆 {'Checking' if is_custom else 'Right now'} : {label}")
        print(f"   Peak hour : {'Yes ⚠️' if display_hour in [17,18,19] else 'No'}")
        print(f"   Weekend   : {'Yes' if display_day in ['Saturday','Sunday'] else 'No'}")
        divider("·")

        result = recommend_time(
            place, temp,
            custom_hour=custom_hour,
            custom_day=custom_day,
        )

        print(f"\n🕐 Recommendation:")

        if result["type"] == "closed":
            crowd = "High"
            print(f"   🔒 Place is CLOSED at {result['hour']}:00")
            print(f"   🕐 Hours : {result['message']}")
            risk = calculate_risk(aqi, temp, crowd)
            print(f"   ⚠️  Risk level : {risk}")

        else:
            if result["type"] == "custom":
                crowd = result["crowd"]
                print(f"   📌 {result['day']} at {result['hour']}:00  →  {result['slot']}")
                print(f"   👥 Expected crowd : {crowd}")

            elif result["type"] == "now":
                crowd = result["crowd"]
                print(f"   ✅ Good to go NOW  →  {result['slot']}")
                print(f"   👥 Expected crowd : {crowd}")

            elif result["type"] == "today":
                crowd = result["crowd"]
                print(f"   ⏳ Better slot today  →  {result['slot']}")
                print(f"   👥 Expected crowd : {crowd}")

            else:
                crowd = result.get("crowd", "High")
                print(f"   ❌ Today's slots are all crowded.")
                if result.get("day") and result.get("slot"):
                    print(f"   📅 Try instead    →  {result['day']}  {result['slot']}")
                    print(f"   👥 Expected crowd : {result['crowd']}")
                else:
                    print(f"   📅 Try a weekday morning for the least crowd.")

            risk = calculate_risk(aqi, temp, crowd)
            print(f"   ⚠️  Risk level     : {risk}")

            final_advice(risk, crowd, aqi, temp, result)

            # ── Transport section ──────────────────────────────────────────
            divider("─")

            # Auto-fetch distance via Google Maps Distance Matrix API
            user_origin   = get_user_origin(user_origin)
            auto_distance = fetch_distance(user_origin, place["place_name"])

            distance_km, priority = ask_transport_preference(auto_distance)

            if distance_km is not None:
                raining = is_raining(aqi, temp)
                transport_result = recommend_transport(
                    distance_km = distance_km,
                    crowd       = crowd,
                    hour        = display_hour,
                    priority    = priority,
                    raining     = raining,
                )
                print_transport_advice(distance_km, transport_result)
            # ── End transport section ──────────────────────────────────────


if __name__ == "__main__":
    main()