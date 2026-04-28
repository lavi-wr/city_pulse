from datetime import datetime
import joblib

# Load encoding maps saved by clean_data.py
day_map   = joblib.load("models/day_map.pkl")
place_map = joblib.load("models/place_map.pkl")
pop_map   = joblib.load("models/pop_map.pkl")
area_map  = joblib.load("models/area_map.pkl")

def build_features(place, temp, hour=None, day_str=None):
    if hour is None:
        hour = datetime.now().hour
    if day_str is None:
        day_str = datetime.now().strftime("%A")

    day        = day_map.get(day_str, 0)
    place_type = place_map.get(place["category"], 0)
    popularity = pop_map.get(place["popularity"], 2)
    area_type  = area_map.get(place["area_type"], 0)

    peak_hour  = 1 if hour in [17, 18, 19] else 0
    weekend    = 1 if day_str in ["Saturday", "Sunday"] else 0

    if   temp < 20: temp_level = 0
    elif temp < 32: temp_level = 1
    else:           temp_level = 2

    return [hour, day, place_type, popularity,
            area_type, peak_hour, weekend, temp_level]
