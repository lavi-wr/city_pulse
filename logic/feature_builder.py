from datetime import datetime

def build_features(place, temp):

    hour = datetime.now().hour
    day_str = datetime.now().strftime("%A")

    day_map = {
        "Monday":0, "Tuesday":1, "Wednesday":2,
        "Thursday":3, "Friday":4, "Saturday":5, "Sunday":6
    }

    place_map = {"Shopping":0, "Tourist":1, "Hybrid":2}
    pop_map = {"Low":1, "Medium":2, "High":3}
    area_map = {"Indoor":0, "Outdoor":1}

    day = day_map[day_str]
    place_type = place_map[place["category"]]
    popularity = pop_map[place["popularity"]]
    area_type = area_map[place["area_type"]]

    peak_hour = 1 if hour in [17,18,19] else 0
    weekend = 1 if day_str in ["Saturday", "Sunday"] else 0

    if temp < 20:
        temp_level = 0
    elif temp < 32:
        temp_level = 1
    else:
        temp_level = 2

    return [
        hour, day, place_type, popularity,
        area_type, peak_hour, weekend, temp_level
    ]