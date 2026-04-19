import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AQI_API_KEY")

def get_aqi(city="delhi"):

    url = f"https://api.waqi.info/feed/{city}/?token={API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if data["status"] != "ok":
            print("AQI API Error:", data)
            return 100

        return data["data"]["aqi"]

    except Exception as e:
        print("AQI API Exception:", e)
        return 100