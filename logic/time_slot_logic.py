from datetime import datetime
from feature_builder import build_features
from crowd_predictor import predict_crowd

TIME_SLOTS = [
    (8,11),
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
        features[5] = 1 if start in [17,18,19] else 0

        crowd = predict_crowd(features)

        if crowd in ["Low", "Medium"]:
            return {
                "type": "now",
                "slot": f"{start}:00 - {end}:00",
                "crowd": crowd
            }

    best_slot = None
    best_score = 10.0
    crowd_prirority = {"Low": 1, "Medium": 2, "High": 3}    

    for start, end in TIME_SLOTS:
        if start<=current_hour:
            continue
        features = build_features(place, temp)
        features[1] = (features[1]+1)%7
        features[0] = start
        features[5] = 1 if start in [17,18,19] else 0

        crowd = predict_crowd(features)
        score = crowd_prirority[crowd]

        if score < best_score:
            best_score = score
            best_slot = {
                "type": "today",
                "slot": f"{start}:00 - {end}:00",
                "crowd": crowd
            }

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
        "message": "No good time today. Try tomorrow morning."
    }