import joblib
import pandas as pd

model = joblib.load("models/crowd_model.pkl")

columns = [
    "hour", "day", "place_type", "popularity",
    "area_type", "peak_hour", "weekend", "temp_level"
]

def predict_crowd(features):

    df = pd.DataFrame([features], columns=columns)

    prediction = model.predict(df)[0]

    mapping = {
        0: "Low",
        1: "Medium",
        2: "High"
    }

    print("FEATURE VECTOR: ",features)
    print("INPUT:", df.values)
    print("PRED:", prediction)
    return mapping[prediction]