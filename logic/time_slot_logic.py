from datetime import datetime
from feature_builder import build_features
from crowd_predictor import predict_crowd

TIME_SLOTS = [
    (8,  11),
    (11, 13),
    (13, 16),
    (16, 19),
    (19, 22),
]

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

def get_current_slot(hour):
    for start, end in TIME_SLOTS:
        if start <= hour < end:
            return (start, end)
    return None

def next_day(day_str):
    idx = DAYS.index(day_str)
    return DAYS[(idx + 1) % 7]

def slot_is_open(start, end, open_hour, close_hour):
    overlap_start = max(start, open_hour)
    overlap_end   = min(end,   close_hour)
    return (overlap_end - overlap_start) >= 1

def is_place_closed(hour, open_hour, close_hour):
    """Returns True if the place is closed at this hour."""
    return hour < open_hour or hour >= close_hour

def best_slot_for_day(place, temp, day_str):
    open_hour  = int(place.get("open_hour",  8))
    close_hour = int(place.get("close_hour", 22))
    crowd_priority = {"Low": 1, "Medium": 2, "High": 3}
    best       = None
    best_score = 99

    for start, end in TIME_SLOTS:
        if not slot_is_open(start, end, open_hour, close_hour):
            continue
        features = build_features(place, temp, hour=start, day_str=day_str)
        crowd    = predict_crowd(features)
        score    = crowd_priority[crowd]
        if score < best_score:
            best_score = score
            best = {"slot": f"{start}:00 - {end}:00", "crowd": crowd, "hour": start}
        if crowd == "Low":
            break

    return best, best_score

def recommend_time(place, temp, custom_hour=None, custom_day=None):
    now          = datetime.now()
    current_hour = custom_hour if custom_hour is not None else now.hour
    day_str      = custom_day  if custom_day  is not None else now.strftime("%A")

    open_hour    = int(place.get("open_hour",  8))
    close_hour   = int(place.get("close_hour", 22))

    # ── ALWAYS check closed first, regardless of custom or right-now ──────────
    if is_place_closed(current_hour, open_hour, close_hour):
        return {
            "type":    "closed",
            "hour":    current_hour,
            "day":     day_str,
            "message": f"Opens {open_hour}:00 – closes {close_hour}:00.",
        }

    # ── Custom time: just evaluate that specific hour ─────────────────────────
    if custom_hour is not None:
        features   = build_features(place, temp, hour=current_hour, day_str=day_str)
        crowd      = predict_crowd(features)
        slot       = get_current_slot(current_hour)
        slot_label = f"{slot[0]}:00 - {slot[1]}:00" if slot else f"{current_hour}:00"
        return {
            "type":  "custom",
            "slot":  slot_label,
            "crowd": crowd,
            "hour":  current_hour,
            "day":   day_str,
        }

    # ── Right now: check current slot first ───────────────────────────────────
    crowd_priority = {"Low": 1, "Medium": 2, "High": 3}

    current_slot = get_current_slot(current_hour)
    if current_slot:
        start, end = current_slot
        if slot_is_open(start, end, open_hour, close_hour):
            features = build_features(place, temp, hour=current_hour, day_str=day_str)
            crowd    = predict_crowd(features)
            if crowd in ["Low", "Medium"]:
                return {
                    "type":  "now",
                    "slot":  f"{start}:00 - {end}:00",
                    "crowd": crowd,
                }

    # ── Look for a better slot later today ───────────────────────────────────
    best_today = None
    best_score = 99

    for start, end in TIME_SLOTS:
        if end <= current_hour:
            continue
        if current_slot and start == current_slot[0]:
            continue
        if not slot_is_open(start, end, open_hour, close_hour):
            continue

        features = build_features(place, temp, hour=start, day_str=day_str)
        crowd    = predict_crowd(features)
        score    = crowd_priority[crowd]

        if score < best_score:
            best_score = score
            best_today = {
                "type":  "today",
                "slot":  f"{start}:00 - {end}:00",
                "crowd": crowd,
            }
        if crowd == "Low":
            break

    if best_today and best_today["crowd"] in ["Low", "Medium"]:
        return best_today

    # ── Look at next 2 days ───────────────────────────────────────────────────
    for days_ahead in [1, 2]:
        target_day = day_str
        for _ in range(days_ahead):
            target_day = next_day(target_day)

        best, score = best_slot_for_day(place, temp, target_day)
        if best and score <= 2:
            return {
                "type":    "another_day",
                "day":     target_day,
                "slot":    best["slot"],
                "crowd":   best["crowd"],
                "message": f"Today's slots are crowded. Best time: {target_day} {best['slot']} ({best['crowd']} crowd).",
            }

    return {
        "type":    "another_day",
        "day":     None,
        "slot":    None,
        "crowd":   "High",
        "message": "All upcoming slots look crowded. Try a weekday morning.",
    }