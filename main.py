import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "api"))
sys.path.insert(0, os.path.join(ROOT, "logic"))

from api.weather_api import get_weather
from api.aqi_api import get_aqi
from logic.time_slot_logic import recommend_time
from logic.advisory_engine import final_advice

import pandas as pd
from datetime import datetime

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]


def divider(char="─", width=44):
    print(char * width)

def aqi_label(aqi):
    if   aqi <= 50:  return "Good 🟢"
    elif aqi <= 100: return "Moderate 🟡"
    elif aqi <= 200: return "Unhealthy 🟠"
    else:            return "Very Unhealthy 🔴"

def calculate_risk(aqi, temp, crowd):
    """
    Risk is driven primarily by crowd, with AQI and temp as modifiers.
    crowd alone sets the baseline: Low=Low, Medium=Moderate only if
    AQI or temp are also bad, High=always at least Moderate.
    """
    if crowd == "Low":
        # Only escalate to Moderate if both AQI and temp are bad
        if aqi > 150 and temp > 35:
            return "Moderate"
        return "Low"

    if crowd == "Medium":
        # Moderate by default; escalate to High if conditions are also bad
        if aqi > 200 or temp > 40:
            return "High"
        return "Moderate"

    # crowd == "High"
    if aqi > 150 or temp > 35:
        return "High"
    return "Moderate"

def show_places(df):
    print("\n📍 Available places:")
    for i, name in enumerate(df["place_name"].tolist(), 1):
        print(f"   {i:>2}. {name}")

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


def main():
    divider("═")
    print("         CITYPULSE — Outing Advisor")
    divider("═")

    print("\n⏳ Fetching live conditions...")
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
            continue

        elif result["type"] == "custom":
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


if __name__ == "__main__":
    main()