# api/weather_api.py

import requests

API_KEY = "7c0c4aa0ea7629c5febfad27d88c0af8"   # 🔴 replace this

def get_weather(city="Delhi"):

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()

        # DEBUG (remove later if you want)
        # print(data)

        if "main" not in data:
            print("Weather API Error:", data)
            return {
                "temperature": 30,   # fallback
                "description": "default"
            }

        return {
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"]
        }

    except Exception as e:
        print("Weather API Exception:", e)
        return {
            "temperature": 30,
            "description": "default"
        }