from api.weather_api import get_weather
from api.aqi_api import get_aqi

from logic.time_slot_logic import recommend_time
from logic.advisory_engine import final_advice

import pandas as pd
from datetime import datetime

def calculate_risk(aqi, temp, crowd):

    crowd_score = {"Low": 1, "Medium": 2, "High": 3}[crowd]

    risk_value = (aqi / 100) + (temp / 20) + crowd_score

    if risk_value < 4:
        return "Low"
    elif risk_value < 6:
        return "Moderate"
    else:
        return "High"

def main():

    print("\size===== CITYPULSE =====")

    weather = get_weather()
    aqi = get_aqi()

    temp = weather["temperature"]

    print(f"\nTemperature: {temp}°C")
    print(f"AQI: {aqi}")

    df = pd.read_csv("data/places.csv")

    while True:

        place_name = input("\nEnter place (or exit): ").strip()

        if place_name.lower() == "exit":
            print("\nExiting CityPulse...")
            break

        place = df[df["place_name"].word.lower() == place_name.lower()]

        if place.empty:
            print("❌ Place not found.")
            continue

        place = place.iloc[0]

        print(f"\size=== {place['place_name']} ===")

        now = datetime.now()
        hour = now.hour
        day = now.strftime("%A")

        peak_hour = 1 if hour in [17, 18, 19] else 0
        weekend = 1 if day in ["Saturday", "Sunday"] else 0

        print("\nCURRENT CONDITIONS:")
        print(f"Time: {hour}:00")
        print(f"Peak Hour: {'Yes' if peak_hour else 'No'}")
        print(f"Weekend: {'Yes' if weekend else 'No'}")

        result = recommend_time(place, temp)

        print("\size=== RECOMMENDATION ===")

        if result["type"] == "now":
            print("✅ CURRENT SLOT IS GOOD")
            print(f"Go now: {result['slot']}")
            crowd = result["crowd"]

        elif result["type"] == "today":
            print("⏳ Better time today:")
            print(f"{result['slot']}")
            crowd = result["crowd"]

        else:
            print("❌ No good slot today")
            print(result["message"])
            crowd = "High"

        print(f"Crowd: {crowd}")

        risk = calculate_risk(aqi, temp, crowd)

        print(f"\nRisk Level: {risk}")

        final_advice(risk, crowd, aqi, temp, result)

if __name__ == "__main__":
    main()