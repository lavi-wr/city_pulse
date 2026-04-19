import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")

def get_weather(city="Delhi"):

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()

        if "main" not in data:
            print("Weather API Error:", data)
            return {"temperature": 30}

        return {"temperature": data["main"]["temp"]}

    except Exception as e:
        print("Weather API Exception:", e)
        return {"temperature": 30}