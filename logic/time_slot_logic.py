from datetime import datetime
from logic.feature_builder import build_features
from logic.crowd_predictor import predict_crowd

TIME_SLOTS = [
    (11, 13),
    (13, 16),
    (16, 19),
    (19, 22)
]

def get_current_slot(hour):
    for start, end in TIME_SLOTS:
        if start <= hour < end:
            return (start, end)
    return None

def recommend_time(place, temp):

    now = datetime.now()
    current_hour = now.hour

    current_slot = get_current_slot(current_hour)

    if current_slot:
        start, end = current_slot

        features = build_features(place, temp)
        features[0] = start

        crowd = predict_crowd(features)

        if crowd in ["Low", "Medium"]:
            return {
                "type": "now",
                "slot": f"{start}:00 - {end}:00",
                "crowd": crowd
            }

    best_slot = None

    for start, end in TIME_SLOTS:

        if end <= current_hour:
            continue

        features = build_features(place, temp)
        features[0] = start

        crowd = predict_crowd(features)

        if crowd in ["Low", "Medium"]:
            best_slot = {
                "type": "today",
                "slot": f"{start}:00 - {end}:00",
                "crowd": crowd
            }
            break

    if best_slot:
        return best_slot

    return {
        "type": "another_day",
        "message": "No good time today. Try tomorrow."
    }