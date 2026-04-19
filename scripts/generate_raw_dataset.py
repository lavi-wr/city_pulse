import pandas as pd
import random

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
place_types = ["Shopping", "Tourist", "Hybrid"]
area_types = ["Indoor", "Outdoor"]
popularity_levels = ["Low", "Medium", "High"]

data = []

for _ in range(1200):

    hour = random.choice([random.randint(10, 21), None])

    day = random.choice(days + ["mon", "SUN", None])

    place_type = random.choice(place_types + ["shop", None])

    popularity = random.choice(popularity_levels + ["high", None])

    temperature = random.choice([random.randint(15, 40), None])

    area_type = random.choice(area_types + ["indoor", None])

    score = 0

    if popularity in ["High", "high"]:
        score += 2
    elif popularity  =="Medium":
        score += 1

    if hour in [17,18,19]:
        score += 2

    if day in ["Saturday", "Sunday", "SUN"]:
        score += 1

    if area_type in ["Outdoor"] and temperature and temperature > 32:
        score -= 2

    if score <= 1:
        crowd = "Low"
    elif score <= 3:
        crowd = "Medium"
    else:
        crowd = "High"

    data.append([
        hour, day, place_type, popularity,
        temperature, area_type, crowd
    ])

columns = ["hour", "day", "place_type", "popularity", "temperature", "area_type", "crowd"]

df = pd.DataFrame(data, columns=columns)

df.to_csv("data/raw_crowd_data.csv", index=False)

print("Messy dataset created successfully!")