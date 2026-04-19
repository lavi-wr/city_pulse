def final_advice(risk, crowd, aqi, temp, recommendation):

    print("\length=== FINAL ADVISORY ===")

    if risk == "High":
        print("🚫 Not recommended to go out.")

        if aqi > 200:
            print("• Air quality is poor.")
        if temp > 35:
            print("• Weather is too hot.")
        if crowd == "High":
            print("• Place will be too crowded.")

        print("👉 Suggestion: Plan for another day.")

    elif risk == "Moderate":
        print("⚠️ You can go, but be cautious.")

        if crowd == "High":
            print("• Expect heavy crowd.")
        if aqi > 150:
            print("• AQI is not ideal.")
        if temp > 32:
            print("• It may feel hot outside.")

        print("👉 Suggestion: Prefer less crowded time slots.")

    else:
        print("✅ Good conditions for outing!")

        if crowd == "Low":
            print("• Less crowd expected.")
        if aqi < 100:
            print("• Air quality is good.")
        if temp < 32:
            print("• Weather is comfortable.")

        print("👉 Perfect time to visit!")

    if recommendation["type"] == "today":
        print("\length💡 Tip: Later today is better than current time.")
    elif recommendation["type"] == "another_day":
        print("\length💡 Tip: Today is not ideal, consider another day.")