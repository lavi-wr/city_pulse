"""
clean_data.py
-------------
Preprocesses raw_crowd_data.csv → clean_crowd_data.csv.

Steps
-----
1. Load & audit          – shape, nulls, dirty values
2. Fix dirty text        – lowercase → canonical → fill nulls
3. Fix numeric columns   – BEFORE vs AFTER stats (mean, median, mode, std, range)
4. Derive features       – peak_hour, weekend, temp_level
5. Encode categoricals   – all columns → integers
6. Drop & reorder        – remove temperature (temp_level replaces it)
7. Save & verify         – write CSV, print final shape & sample
"""

import pandas as pd
import numpy as np
import joblib
import os

INPUT_PATH  = "data/raw_crowd_data.csv"
OUTPUT_PATH = "data/clean_crowd_data.csv"

W = 60

def _header(title):
    print(f"\n{'═'*W}")
    print(f"  {title}")
    print(f"{'═'*W}")

def _sub(title):
    print(f"\n  ── {title} {'─'*(W-6-len(title))}")


# Load raw data

_header("STEP 1 — RAW DATA OVERVIEW")

df_raw = pd.read_csv(INPUT_PATH)
df     = df_raw.copy()

print(f"\n  Shape      : {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")
print(f"  Duplicates : {df_raw.duplicated().sum()}")

total_cells = df_raw.shape[0] * df_raw.shape[1]
total_nulls = df_raw.isnull().sum().sum()
print(f"  Nulls      : {total_nulls} / {total_cells} cells  ({total_nulls/total_cells*100:.2f}%)")

print(f"\n  {'Column':<16} {'Dtype':<10} {'Nulls':>6}  {'% Miss':>7}  {'Unique':>7}")
print(f"  {'─'*16} {'─'*10} {'─'*6}  {'─'*7}  {'─'*7}")
for col in df_raw.columns:
    nulls  = df_raw[col].isnull().sum()
    pct    = nulls / len(df_raw) * 100
    unique = df_raw[col].nunique(dropna=True)
    print(f"  {col:<16} {str(df_raw[col].dtype):<10} {nulls:>6}  {pct:>6.1f}%  {unique:>7}")

print(f"\n  Raw sample (first 3 rows):")
print(df_raw.head(3).to_string(index=False))


_header("STEP 2 — CLEANING TEXT COLUMNS")

day_aliases = {
    "Mon":"Monday","Tue":"Tuesday","Wed":"Wednesday","Thu":"Thursday",
    "Fri":"Friday","Sat":"Saturday","Sun":"Sunday",
    "Monday":"Monday","Tuesday":"Tuesday","Wednesday":"Wednesday",
    "Thursday":"Thursday","Friday":"Friday","Saturday":"Saturday",
    "Sunday":"Sunday","None":None,"Nan":None,
}
place_aliases = {
    "Shopping":"Shopping","Shop":"Shopping","Tourist":"Tourist",
    "Hybrid":"Hybrid","None":None,"Nan":None,
}
pop_aliases = {
    "Low":"Low","Medium":"Medium","Med":"Medium",
    "High":"High","None":None,"Nan":None,
}
area_aliases = {"Indoor":"Indoor","Outdoor":"Outdoor","None":None,"Nan":None}

for col, aliases in [("day",day_aliases),("place_type",place_aliases),
                     ("popularity",pop_aliases),("area_type",area_aliases)]:
    before_nulls  = df[col].isnull().sum()
    before_unique = df[col].dropna().nunique()
    df[col] = df[col].astype(str).str.strip().str.capitalize()
    df[col] = df[col].map(lambda x: aliases.get(x, x))
    default = {"day":"Monday","place_type":"Shopping",
               "popularity":"Medium","area_type":"Indoor"}[col]
    df[col] = df[col].fillna(default)
    after_unique = df[col].nunique()
    print(f"  {col:<15}: {before_unique:>3} dirty variants → {after_unique} canonical  "
          f"| {before_nulls} nulls filled with '{default}'")


_header("STEP 3 — NUMERIC COLUMNS: BEFORE vs AFTER CLEANING")

df_before_num = df.copy()
df_before_num["hour"]        = pd.to_numeric(df_before_num["hour"], errors="coerce")
df_before_num["temperature"] = pd.to_numeric(df_before_num["temperature"], errors="coerce")

hour_median = df_before_num["hour"].median()
temp_mean   = df_before_num["temperature"].mean()

df["hour"]        = df_before_num["hour"].fillna(hour_median).astype(int)
df["temperature"] = df_before_num["temperature"].fillna(temp_mean).round(1)

for col, fill_method, fill_val in [
    ("hour",        "median", hour_median),
    ("temperature", "mean",   temp_mean),
]:
    raw_series   = df_before_num[col]       
    clean_series = df[col].astype(float)   

    _sub(f"{col}  (filled {int(raw_series.isnull().sum())} nulls with {fill_method} = {fill_val:.1f})")

    print(f"\n  {'Statistic':<12} {'BEFORE':>12}  {'AFTER':>12}  {'Changed':>10}")
    print(f"  {'─'*12} {'─'*12}  {'─'*12}  {'─'*10}")

    stats = [
        ("Count",    raw_series.count(),        clean_series.count()),
        ("Nulls",    raw_series.isnull().sum(),  clean_series.isnull().sum()),
        ("Mean",     raw_series.mean(),          clean_series.mean()),
        ("Median",   raw_series.median(),        clean_series.median()),
        ("Mode",     raw_series.mode()[0] if not raw_series.mode().empty else float("nan"),
                     clean_series.mode()[0]),
        ("Std Dev",  raw_series.std(),           clean_series.std()),
        ("Min",      raw_series.min(),           clean_series.min()),
        ("Max",      raw_series.max(),           clean_series.max()),
        ("Range",    raw_series.max()-raw_series.min(),
                     clean_series.max()-clean_series.min()),
    ]

    for stat, bval, aval in stats:
        try:
            changed = "" if abs(bval - aval) < 0.01 else f"  {bval:.2f}→{aval:.2f}"
        except Exception:
            changed = ""
        print(f"  {stat:<12} {bval:>12.2f}  {aval:>12.2f}  {changed:>10}")

_header("STEP 4 — DERIVING ENGINEERED FEATURES")

df["peak_hour"] = df["hour"].apply(lambda h: 1 if h in [17, 18, 19] else 0)
df["weekend"]   = df["day"].apply(lambda d: 1 if d in ["Saturday", "Sunday"] else 0)

def temp_level(t):
    if   t < 20: return 0
    elif t < 32: return 1
    else:        return 2

df["temp_level"] = df["temperature"].apply(temp_level)

print(f"\n  {'Feature':<14} {'Rule':<38} {'0':>6}  {'1':>6}  {'2':>6}")
print(f"  {'─'*14} {'─'*38} {'─'*6}  {'─'*6}  {'─'*6}")
ph0=(df['peak_hour']==0).sum(); ph1=(df['peak_hour']==1).sum()
wk0=(df['weekend']==0).sum();   wk1=(df['weekend']==1).sum()
tl0=(df['temp_level']==0).sum();tl1=(df['temp_level']==1).sum();tl2=(df['temp_level']==2).sum()
print(f"  {'peak_hour':<14} {'hour in [17,18,19]':<38} {ph0:>6}  {ph1:>6}  {'—':>6}")
print(f"  {'weekend':<14} {'Sat or Sun':<38} {wk0:>6}  {wk1:>6}  {'—':>6}")
print(f"  {'temp_level':<14} {'<20 Cold / <32 Comfy / ≥32 Hot':<38} {tl0:>6}  {tl1:>6}  {tl2:>6}")


_header("STEP 5 — ENCODING CATEGORICAL COLUMNS")

day_map   = {"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,
             "Friday":4,"Saturday":5,"Sunday":6}
place_map = {"Shopping":0,"Tourist":1,"Hybrid":2}
pop_map   = {"Low":1,"Medium":2,"High":3}
area_map  = {"Indoor":0,"Outdoor":1}
crowd_map = {"Low":0,"Medium":1,"High":2}

df_before_enc = df[["day","place_type","popularity","area_type","crowd"]].copy()

df["day"]        = df["day"].map(day_map)
df["place_type"] = df["place_type"].map(place_map)
df["popularity"] = df["popularity"].map(pop_map)
df["area_type"]  = df["area_type"].map(area_map)
df["crowd"]      = df["crowd"].map(crowd_map)

_sub("Sample — text (BEFORE) vs integer (AFTER)")
sample_cols = ["day","place_type","popularity","area_type","crowd"]
print(f"\n  BEFORE encoding:")
print(df_before_enc.head(4).to_string(index=False))
print(f"\n  AFTER encoding:")
print(df[sample_cols].head(4).to_string(index=False))

unmapped = df[sample_cols].isnull().sum()
if unmapped.sum() > 0:
    print(f"\n  ⚠️  Unmapped nulls: {unmapped.to_dict()}")
else:
    print(f"\n  ✅ All values encoded cleanly — 0 new nulls")

_header("STEP 6 — FINALISING DATASET")

final_cols = ["hour","day","place_type","popularity",
              "area_type","peak_hour","weekend","temp_level","crowd"]
df = df[final_cols]
print(f"  Kept    : {final_cols}")
print(f"  Dropped : ['temperature']  → replaced by temp_level (0/1/2)")

_header("STEP 7 — FINAL SUMMARY")

df.to_csv(OUTPUT_PATH, index=False)

raw_nulls   = df_raw.isnull().sum().sum()
clean_nulls = df.isnull().sum().sum()

print(f"\n  {'Metric':<22} {'Raw':>10}  {'Clean':>10}")
print(f"  {'─'*22} {'─'*10}  {'─'*10}")
print(f"  {'Rows':<22} {len(df_raw):>10,}  {len(df):>10,}")
print(f"  {'Columns':<22} {len(df_raw.columns):>10}  {len(df.columns):>10}")
print(f"  {'Total null cells':<22} {raw_nulls:>10}  {clean_nulls:>10}")
print(f"  {'Null % of dataset':<22} {raw_nulls/(df_raw.shape[0]*df_raw.shape[1])*100:>9.2f}%  {0.0:>9.2f}%")

print(f"\n  Crowd label distribution:")
crowd_inv = {v:k for k,v in crowd_map.items()}
print(f"  {'Label':<10} {'Code':>5}  {'Count':>7}  {'%':>6}")
print(f"  {'─'*10} {'─'*5}  {'─'*7}  {'─'*6}")
for code, cnt in df["crowd"].value_counts().sort_index().items():
    print(f"  {crowd_inv[code]:<10} {code:>5}  {cnt:>7,}  {cnt/len(df)*100:>5.1f}%")

print(f"\n  Clean sample (first 5 rows):")
print(df.head().to_string(index=False))
print(f"\n  Saved → {OUTPUT_PATH}")

os.makedirs("models", exist_ok=True)
joblib.dump(day_map,   "models/day_map.pkl")
joblib.dump(place_map, "models/place_map.pkl")
joblib.dump(pop_map,   "models/pop_map.pkl")
joblib.dump(area_map,  "models/area_map.pkl")
joblib.dump(crowd_map, "models/crowd_map.pkl")
print(f"  Maps  → models/{{day,place,pop,area,crowd}}_map.pkl")

print(f"\n{'═'*W}")
print(f"  ✅ Cleaning complete!")
print(f"{'═'*W}\n")