"""
clean_data.py
-------------
Preprocesses raw_crowd_data.csv → clean_crowd_data.csv.

Steps
-----
1. Load & audit          – shape, nulls, dirty values
2. Fix dirty text        – lowercase → canonical → fill nulls
3. Fix numeric columns   – fill nulls with median / mean
4. Derive features       – peak_hour, weekend, temp_level
5. Encode categoricals   – all columns → integers
6. Drop & reorder        – remove temperature (temp_level replaces it)
7. Save & verify         – write CSV, print final shape & sample
"""

import pandas as pd
import numpy as np

INPUT_PATH  = "data/raw_crowd_data.csv"
OUTPUT_PATH = "data/clean_crowd_data.csv"


def _header(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ══════════════════════════════════════════════════════════
# STEP 1 – Load & audit
# ══════════════════════════════════════════════════════════

_header("STEP 1 — Loading raw data")
df = pd.read_csv(INPUT_PATH)

print(f"  Raw shape          : {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"  Total null cells   : {df.isnull().sum().sum()}")
print(f"\n  Null breakdown:")
for col, cnt in df.isnull().sum().items():
    pct = cnt / len(df) * 100
    print(f"    {col:<15}: {cnt:>4} nulls  ({pct:.1f}%)")

initial_rows = len(df)


# ══════════════════════════════════════════════════════════
# STEP 2 – Fix dirty text columns
# ══════════════════════════════════════════════════════════

_header("STEP 2 — Cleaning text columns")

# ── day ──────────────────────────────────────────────────
df["day"] = df["day"].astype(str).str.strip().str.capitalize()
day_aliases = {
    "Mon":       "Monday",
    "Tue":       "Tuesday",
    "Wed":       "Wednesday",
    "Thu":       "Thursday",
    "Fri":       "Friday",
    "Sat":       "Saturday",
    "Sun":       "Sunday",
    "Monday":    "Monday",  "Tuesday": "Tuesday", "Wednesday": "Wednesday",
    "Thursday":  "Thursday","Friday":  "Friday",  "Saturday":  "Saturday",
    "Sunday":    "Sunday",  "None":    None,       "Nan":       None,
}
df["day"] = df["day"].map(lambda x: day_aliases.get(x, x))
df["day"] = df["day"].fillna("Monday")
print(f"  day      → unique values after clean: {sorted(df['day'].unique())}")

# ── place_type ───────────────────────────────────────────
df["place_type"] = df["place_type"].astype(str).str.strip().str.capitalize()
place_aliases = {
    "Shopping": "Shopping", "Shop":     "Shopping",
    "Tourist":  "Tourist",
    "Hybrid":   "Hybrid",
    "None":     None,       "Nan":      None,
}
df["place_type"] = df["place_type"].map(lambda x: place_aliases.get(x, x))
df["place_type"] = df["place_type"].fillna("Shopping")
print(f"  place_type → unique: {sorted(df['place_type'].unique())}")

# ── popularity ───────────────────────────────────────────
df["popularity"] = df["popularity"].astype(str).str.strip().str.capitalize()
pop_aliases = {
    "Low": "Low", "Medium": "Medium", "Med": "Medium",
    "High": "High",
    "None": None, "Nan": None,
}
df["popularity"] = df["popularity"].map(lambda x: pop_aliases.get(x, x))
df["popularity"] = df["popularity"].fillna("Medium")
print(f"  popularity → unique: {sorted(df['popularity'].unique())}")

# ── area_type ────────────────────────────────────────────
df["area_type"] = df["area_type"].astype(str).str.strip().str.capitalize()
area_aliases = {
    "Indoor": "Indoor", "Outdoor": "Outdoor",
    "None": None, "Nan": None,
}
df["area_type"] = df["area_type"].map(lambda x: area_aliases.get(x, x))
df["area_type"] = df["area_type"].fillna("Indoor")
print(f"  area_type  → unique: {sorted(df['area_type'].unique())}")


# ══════════════════════════════════════════════════════════
# STEP 3 – Fix numeric columns
# ══════════════════════════════════════════════════════════

_header("STEP 3 — Fixing numeric columns")

hour_median = df["hour"].median()
temp_mean   = df["temperature"].mean()

df["hour"]        = pd.to_numeric(df["hour"], errors="coerce")
df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")

df["hour"]        = df["hour"].fillna(hour_median).astype(int)
df["temperature"] = df["temperature"].fillna(temp_mean).round(1)

print(f"  hour        → filled nulls with median  ({hour_median:.0f})")
print(f"  temperature → filled nulls with mean    ({temp_mean:.1f}°C)")
print(f"  hour range  : {df['hour'].min()} – {df['hour'].max()}")
print(f"  temp range  : {df['temperature'].min()} – {df['temperature'].max()} °C")


# ══════════════════════════════════════════════════════════
# STEP 4 – Derive engineered features
# ══════════════════════════════════════════════════════════

_header("STEP 4 — Deriving engineered features")

df["peak_hour"] = df["hour"].apply(lambda h: 1 if h in [17, 18, 19] else 0)
df["weekend"]   = df["day"].apply(lambda d: 1 if d in ["Saturday", "Sunday"] else 0)

def temp_level(t):
    if   t < 20: return 0   # Cold
    elif t < 32: return 1   # Comfortable
    else:        return 2   # Hot

df["temp_level"] = df["temperature"].apply(temp_level)

print(f"  peak_hour  : {df['peak_hour'].sum():>5} rows flagged as peak   ({df['peak_hour'].mean()*100:.1f}%)")
print(f"  weekend    : {df['weekend'].sum():>5} rows flagged as weekend ({df['weekend'].mean()*100:.1f}%)")
print(f"  temp_level : {df['temp_level'].value_counts().sort_index().to_dict()}")


# ══════════════════════════════════════════════════════════
# STEP 5 – Encode categoricals
# ══════════════════════════════════════════════════════════

_header("STEP 5 — Encoding categorical columns")

day_map       = {"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,
                 "Friday":4,"Saturday":5,"Sunday":6}
place_map     = {"Shopping":0,"Tourist":1,"Hybrid":2}
pop_map       = {"Low":1,"Medium":2,"High":3}
area_map      = {"Indoor":0,"Outdoor":1}
crowd_map     = {"Low":0,"Medium":1,"High":2}

df["day"]        = df["day"].map(day_map)
df["place_type"] = df["place_type"].map(place_map)
df["popularity"] = df["popularity"].map(pop_map)
df["area_type"]  = df["area_type"].map(area_map)
df["crowd"]      = df["crowd"].map(crowd_map)

# Check for any unmapped values (would show as NaN)
unmapped = df[["day","place_type","popularity","area_type","crowd"]].isnull().sum()
if unmapped.sum() > 0:
    print(f"  ⚠️  Unmapped values introduced nulls:\n{unmapped}")
else:
    print("  ✅ All categorical values mapped successfully")

for col, mapping in [("day", day_map), ("place_type", place_map),
                     ("popularity", pop_map), ("area_type", area_map),
                     ("crowd", crowd_map)]:
    print(f"  {col:<15}: {mapping}")


# ══════════════════════════════════════════════════════════
# STEP 6 – Final column selection & ordering
# ══════════════════════════════════════════════════════════

_header("STEP 6 — Finalising dataset")

final_cols = ["hour", "day", "place_type", "popularity",
              "area_type", "peak_hour", "weekend", "temp_level", "crowd"]
df = df[final_cols]

print(f"  Dropped  : ['temperature']  (replaced by temp_level)")
print(f"  Final columns : {final_cols}")


# ══════════════════════════════════════════════════════════
# STEP 7 – Save & verify
# ══════════════════════════════════════════════════════════

_header("STEP 7 — Saving clean dataset")

df.to_csv(OUTPUT_PATH, index=False)

print(f"  Saved to   : {OUTPUT_PATH}")
print(f"  Final shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"  Remaining nulls: {df.isnull().sum().sum()}")
print(f"\n  Crowd label balance:")
crowd_inv = {v: k for k, v in crowd_map.items()}
for code, cnt in df["crowd"].value_counts().sort_index().items():
    pct = cnt / len(df) * 100
    print(f"    {crowd_inv[code]:<8} ({code}): {cnt:>5}  ({pct:.1f}%)")

print(f"\n  Sample (first 5 rows):")
print(df.head().to_string(index=False))
print(f"\n✅ Cleaning complete!")

import joblib
import os

os.makedirs("models", exist_ok=True)

joblib.dump(day_map, "models/day_map.pkl")
joblib.dump(place_map, "models/place_map.pkl")
joblib.dump(pop_map, "models/pop_map.pkl")
joblib.dump(area_map, "models/area_map.pkl")
joblib.dump(crowd_map, "models/crowd_map.pkl")