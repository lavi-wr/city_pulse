import pandas as pd

# LOAD DATA
df = pd.read_csv("data/raw_crowd_data.csv")

print("Before Cleaning:\n")
print(df.head())

# -------------------------------
# 1. HANDLE MISSING VALUES
# -------------------------------

df["hour"] = df["hour"].fillna(df["hour"].median())

df["temperature"] = df["temperature"].fillna(df["temperature"].mean())

df["day"] = df["day"].fillna("Monday")

df["place_type"] = df["place_type"].fillna("Shopping")

df["popularity"] = df["popularity"].fillna("Medium")

df["area_type"] = df["area_type"].fillna("Indoor")

# -------------------------------
# 2. FIX INCONSISTENT VALUES
# -------------------------------

# day cleaning
df["day"] = df["day"].str.capitalize()
df["day"] = df["day"].replace({
    "Mon": "Monday",
    "Sun": "Sunday"
})

# place_type cleaning
df["place_type"] = df["place_type"].replace({
    "shop": "Shopping"
})

# popularity cleaning
df["popularity"] = df["popularity"].str.capitalize()

# area_type cleaning
df["area_type"] = df["area_type"].str.capitalize()

# -------------------------------
# 3. FEATURE ENGINEERING
# -------------------------------

# peak hour
df["peak_hour"] = df["hour"].apply(lambda x: 1 if x in [17,18,19] else 0)

# weekend
df["weekend"] = df["day"].apply(lambda x: 1 if x in ["Saturday", "Sunday"] else 0)

# temp_level
def temp_level(temp):
    if temp < 20:
        return 0
    elif temp < 32:
        return 1
    else:
        return 2

df["temp_level"] = df["temperature"].apply(temp_level)

# -------------------------------
# 4. ENCODING
# -------------------------------

# day
day_map = {
    "Monday":0, "Tuesday":1, "Wednesday":2,
    "Thursday":3, "Friday":4, "Saturday":5, "Sunday":6
}
df["day"] = df["day"].map(day_map)

# place_type
place_map = {"Shopping":0, "Tourist":1, "Hybrid":2}
df["place_type"] = df["place_type"].map(place_map)

# popularity
pop_map = {"Low":1, "Medium":2, "High":3}
df["popularity"] = df["popularity"].map(pop_map)

# area_type
area_map = {"Indoor":0, "Outdoor":1}
df["area_type"] = df["area_type"].map(area_map)

# crowd (target)
crowd_map = {"Low":0, "Medium":1, "High":2}
df["crowd"] = df["crowd"].map(crowd_map)

# -------------------------------
# 5. DROP UNUSED
# -------------------------------

df = df.drop(columns=["temperature"])

# -------------------------------
# SAVE CLEAN DATA
# -------------------------------

df.to_csv("data/clean_crowd_data.csv", index=False)

print("\nAfter Cleaning:\n")
print(df.head())

print("\nCleaning completed successfully!")