"""
main.py
-------
CityPulse — Smart outing advisor for Delhi/NCR.

Run from the project root (city_pulse/):
    python main.py

Requires:
    - .env file with AQI_API_KEY and WEATHER_API_KEY  (fallbacks used if missing)
    - models/crowd_model.pkl  (run scripts/train_model.py first)
    - data/places.csv         (included in project)
"""

import sys
import os

# ── Anchor all paths and imports to the project root ─────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

# Add api/ and logic/ folders to Python's import search path
sys.path.insert(0, os.path.join(ROOT, "api"))
sys.path.insert(0, os.path.join(ROOT, "logic"))

# ── Imports ───────────────────────────────────────────────────────────────────
from weather_api import get_weather
from aqi_api import get_aqi

from time_slot_logic import recommend_time
from advisory_engine import final_advice

import pandas as pd
from datetime import datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

def calculate_risk(aqi, temp, crowd):
    crowd_score = {"Low": 1, "Medium": 2, "High": 3}[crowd]
    risk_value  = (aqi / 100) + (temp / 20) + crowd_score

    if   risk_value < 4: return "Low"
    elif risk_value < 6: return "Moderate"
    else:                return "High"


def print_divider(char="─", width=40):
    print(char * width)


def aqi_label(aqi):
    if   aqi <= 50:  return "Good 🟢"
    elif aqi <= 100: return "Moderate 🟡"
    elif aqi <= 200: return "Unhealthy 🟠"
    else:            return "Very Unhealthy 🔴"


def show_available_places(df):
    print("\n📍 Available places:")
    for i, name in enumerate(df["place_name"].tolist(), 1):
        print(f"   {i:>2}. {name}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print_divider("═")
    print("         CITYPULSE — Outing Advisor")
    print_divider("═")

    # ── Live data ─────────────────────────────────────────────────────────────
    print("\n⏳ Fetching live conditions...")
    weather = get_weather()
    aqi     = get_aqi()
    temp    = weather["temperature"]

    now  = datetime.now()
    hour = now.hour
    day  = now.strftime("%A")

    print(f"\n📅 {day}  🕐 {now.strftime('%H:%M')}")
    print(f"🌡️  Temperature : {temp}°C")
    print(f"💨 AQI         : {aqi}  ({aqi_label(aqi)})")

    # ── Load places ───────────────────────────────────────────────────────────
    places_path = os.path.join(ROOT, "data", "places.csv")
    try:
        df = pd.read_csv(places_path)
    except FileNotFoundError:
        print(f"\n❌ places.csv not found at: {places_path}")
        return

    show_available_places(df)

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        print()
        print_divider()
        place_name = input("Enter place name (or 'exit'): ").strip()

        if place_name.lower() == "exit":
            print("\n👋 Exiting CityPulse. Have a great day!")
            break

        match = df[df["place_name"].str.lower() == place_name.lower()]

        if match.empty:
            print(f"❌ '{place_name}' not found. Type a name from the list above.")
            continue

        place = match.iloc[0]

        print_divider("─")
        print(f"📍 {place['place_name']}")
        print(f"   Category   : {place['category']}")
        print(f"   Popularity : {place['popularity']}")
        print(f"   Area type  : {place['area_type']}")

        peak_hour = 1 if hour in [17, 18, 19] else 0
        weekend   = 1 if day in ["Saturday", "Sunday"] else 0

        print(f"\n⚙️  Current Conditions:")
        print(f"   Peak hour  : {'Yes ⚠️' if peak_hour else 'No'}")
        print(f"   Weekend    : {'Yes' if weekend else 'No'}")

        result = recommend_time(place, temp)

        print(f"\n🕐 Time Recommendation:")
        if result["type"] == "now":
            print(f"   ✅ Go NOW  →  {result['slot']}")
            crowd = result["crowd"]
        elif result["type"] == "today":
            print(f"   ⏳ Better later today  →  {result['slot']}")
            crowd = result["crowd"]
        else:
            print(f"   ❌ {result['message']}")
            crowd = "High"

        print(f"   👥 Crowd   : {crowd}")

        risk = calculate_risk(aqi, temp, crowd)
        print(f"   ⚠️  Risk    : {risk}")

        final_advice(risk, crowd, aqi, temp, result)


if __name__ == "__main__":
    main()