"""
generate_raw_dataset.py
-----------------------
Generates a realistic synthetic dataset that mirrors real-world crowd patterns
observed in urban Indian locations (malls, tourist spots, hybrid venues).

Distribution logic is grounded in:
  - Delhi NCR retail traffic studies (peak: Sat/Sun evenings)
  - India Meteorological Dept seasonal ranges for Delhi
  - Standard place-type visit patterns (tourist sites busier on weekends, etc.)

The dataset is intentionally messy (missing values, typos, mixed cases)
so that the preprocessing pipeline has real work to do.
"""

import pandas as pd
import numpy as np
import random
import os

random.seed(42)
np.random.seed(42)

# ── Constants ──────────────────────────────────────────────────────────────────

DAYS            = ["Monday", "Tuesday", "Wednesday", "Thursday",
                   "Friday", "Saturday", "Sunday"]
PLACE_TYPES     = ["Shopping", "Tourist", "Hybrid"]
AREA_TYPES      = ["Indoor", "Outdoor"]
POPULARITY      = ["Low", "Medium", "High"]
HOURS           = list(range(9, 23))          # 9 AM – 10 PM
N_SAMPLES       = 5000

# Delhi temperature ranges by month (°C), based on IMD data
MONTHLY_TEMPS   = {
    1:  (8,  20),  2:  (11, 23),  3: (16, 29),  4: (21, 36),
    5:  (26, 41),  6:  (28, 40),  7: (27, 35),  8: (26, 34),
    9:  (24, 33), 10:  (19, 30), 11: (13, 25), 12: (9,  20),
}

# Realistic crowd weights by (hour, day_type, place_type)
def base_crowd_score(hour, day, place_type, popularity, temp,area_type):
    """Returns a 0-10 crowd score based on real-world heuristics."""
    score = 0.0

    # Popularity baseline
    score += {"Low": 1.0, "Medium": 2.5, "High": 3.5}[popularity]

    # Hour-of-day effect (bimodal: lunch + evening peaks)
    if hour<=11:
        score-=2.0
    elif   12 <= hour <= 14: score += 2.0      # lunch rush
    elif 17 <= hour <= 21: score += 2.2      # evening peak
    elif 10 <= hour <= 11: score += 1.0      # morning opener
    elif hour >= 22:       score -= 3.0      # winding down
    elif hour >=21:        score -= 1.5      # late night drop

    # Weekday / weekend effect
    if day in ["Saturday", "Sunday"]:
        score += 1.5
    elif day == "Friday":
        score += 1.0

    # Place-type interaction
    if place_type == "Shopping":
        score += 2.0
        if day in ["Saturday", "Sunday"]:
           score += 1.5

    if place_type == "Tourist":
       score += 1.5
       if day in ["Saturday", "Sunday"]:
           score += 2.5

    if place_type == "Hybrid":
       score += 1.0  

    if place_type == "Tourist" and random.random()<0.3:
        score-=2.0
    
    if place_type == "Shopping" and popularity == "Low":
        score-=2.0
    # Area effect (important for realism)
    if area_type == "Outdoor":
        if temp > 34:
            score -= 2.0   # heat reduces outdoor visits
        elif 22 <= temp <= 30:
            score += 1.0   # pleasant weather boosts outdoor

    if area_type == "Indoor":
        if temp > 34:
            score += 1.5   # malls benefit in heat

    if area_type == "Indoor" and hour >= 22:
        score-=3.5  # late night indoor venues close early

    if area_type == "Outdoor" and hour >= 22:
        score-=2.5  # outdoor venues close early, more so than indoor

    # Temperature impact (extreme heat/cold reduces outdoor visits)
    if temp > 38:
        score -= 2.5
    elif temp > 34:
        score -= 1.0
    elif 22 <= temp <= 30:
        score += 0.5          # comfortable weather → more visitors

    if day in ["Saturday", "Sunday"] and random.random()<0.25:
        score-=2.5

    return score


def score_to_crowd(score):
    if score <= 4.5:  return "Low"
    if score <= 7.5:  return "Medium"
    return "High"


def inject_noise(value, choices, null_prob=0.04, dirty_map=None):
    """Randomly introduces nulls and dirty variants."""
    if random.random() < null_prob:
        return None
    if dirty_map and random.random() < 0.06:
        return random.choice(dirty_map.get(value, [value]))
    return value


# ── Data Generation ────────────────────────────────────────────────────────────

rows = []

for _ in range(N_SAMPLES):

    month       = random.randint(1, 12)
    tmin, tmax  = MONTHLY_TEMPS[month]
    temp_true   = round(np.random.uniform(tmin, tmax), 1)

    day_true    = random.choices(
        DAYS,
        weights=[10, 10, 10, 10, 12, 16, 14],   # Weekends more likely
        k=1
    )[0]

    hour_true   = random.choices(
        HOURS,
        weights=[3, 5, 8, 12, 15, 15, 14, 12, 10, 7, 4, 3, 2, 1],  # peaks at 17-20
        k=1
    )[0]

    place_type_true = random.choices(
        PLACE_TYPES, weights=[50, 30, 20], k=1
    )[0]

    popularity_true = random.choices(
        POPULARITY, weights=[20, 45, 35], k=1
    )[0]

    area_type_true = (
        "Indoor" if place_type_true == "Shopping"
        else random.choices(AREA_TYPES, weights=[35, 65], k=1)[0]
    )

    score = base_crowd_score(
        hour_true, day_true, place_type_true, popularity_true, temp_true, area_type_true
    )
    # Add Gaussian noise
    score += np.random.normal(0, 1.2)
    crowd_true = score_to_crowd(score)

    # ── Inject messiness ──────────────────────────────────────────────────────
    hour  = inject_noise(hour_true, HOURS, null_prob=0.03)

    day   = inject_noise(day_true, DAYS, null_prob=0.04, dirty_map={
        "Monday":    ["monday", "Mon", "MON"],
        "Tuesday":   ["Tue", "tue"],
        "Wednesday": ["Wed", "wed", "WEDNESDAY"],
        "Saturday":  ["Sat", "sat", "SAT"],
        "Sunday":    ["Sun", "SUN", "sun"],
    })

    place_type = inject_noise(place_type_true, PLACE_TYPES, null_prob=0.04, dirty_map={
        "Shopping": ["shopping", "shop", "SHOPPING"],
        "Tourist":  ["tourist", "TOURIST"],
        "Hybrid":   ["hybrid", "HYBRID"],
    })

    popularity = inject_noise(popularity_true, POPULARITY, null_prob=0.04, dirty_map={
        "Low":    ["low", "LOW"],
        "Medium": ["medium", "med", "MEDIUM"],
        "High":   ["high", "HIGH"],
    })

    temp = inject_noise(round(temp_true + np.random.normal(0, 0.3), 1),
                        [], null_prob=0.04)

    area_type = inject_noise(area_type_true, AREA_TYPES, null_prob=0.04, dirty_map={
        "Indoor":  ["indoor", "INDOOR"],
        "Outdoor": ["outdoor", "OUTDOOR"],
    })

    rows.append([hour, day, place_type, popularity, temp, area_type, crowd_true])


# ── Save ───────────────────────────────────────────────────────────────────────

os.makedirs("data", exist_ok=True)
columns = ["hour", "day", "place_type", "popularity", "temperature", "area_type", "crowd"]
df = pd.DataFrame(rows, columns=columns)
df.to_csv("data/raw_crowd_data.csv", index=False)

print(f"✅  Raw dataset created: {len(df):,} rows × {len(df.columns)} columns")
print(f"    Nulls injected  → {df.isnull().sum().sum()} cells")
print(f"    Crowd split     → {df['crowd'].value_counts().to_dict()}")