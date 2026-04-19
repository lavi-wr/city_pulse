# api/aqi_api.py

import requests

API_KEY = "demo"   # works without signup

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