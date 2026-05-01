def final_advice(risk, crowd, aqi, temp, recommendation):

    print("\n=== FINAL ADVISORY ===")

    if risk == "High":
        print("🚫 Not recommended to go out.")
        if aqi > 200:   print("  • Air quality is very poor.")
        if temp > 38:   print("  • Dangerously hot outside.")
        elif temp > 35: print("  • Weather is too hot.")
        if crowd == "High": print("  • Place will be very crowded.")
        print("👉 Plan for a better day or time.")

    elif risk == "Moderate":
        print("⚠️  Conditions are okay, but not ideal.")
        if crowd == "High":   print("  • Expect heavy crowd.")
        if 150 < aqi <= 200:  print("  • AQI is getting unhealthy.")
        if temp > 35:         print("  • It will feel very hot outside.")
        elif temp > 32:       print("  • It may feel warm outside.")
        print("👉 You can go — prefer an off-peak slot if possible.")

    else:
        # Low risk
        print("✅ Great conditions for an outing!")
        if crowd == "Low":   print("  • Low crowd expected — enjoy the space.")
        if aqi < 50:         print("  • Air quality is excellent.")
        elif aqi < 100:      print("  • Air quality is good.")
        if temp < 20:        print("  • It'll be cool — carry a jacket.")
        elif temp < 32:      print("  • Weather is comfortable.")
        print("👉 Perfect time to visit!")

    rec_type = recommendation.get("type")

    if rec_type == "now":
        pass   

    elif rec_type == "today":
        slot = recommendation.get("slot", "")
        c    = recommendation.get("crowd", "")
        print(f"\n💡 Better slot later today: {slot}  ({c} crowd)")

    elif rec_type == "another_day":
        day  = recommendation.get("day")
        slot = recommendation.get("slot")
        c    = recommendation.get("crowd", "")
        if day and slot:
            print(f"\n💡 Best upcoming slot: {day}  {slot}  ({c} crowd)")
        else:
            print("\n💡 Try a weekday morning for the least crowd.")

    elif rec_type == "custom":
        pass   