# 🌆 CityPulse

CityPulse is an AI-based smart city assistant that helps users decide the best time to visit places based on:

- Weather 🌤
- Air Quality 🌫
- Crowd Prediction (Machine Learning) 👥

---

## 🚀 Features

- Real-time weather & AQI using APIs
- ML-based crowd prediction
- Smart time-slot recommendation
- Risk analysis (Low / Moderate / High)
- Final advisory system

---

## 🧠 Tech Stack

- Python
- Pandas
- Scikit-learn (Decision Tree)
- REST APIs

---

## ▶️ How to Run

```bash
pip install -r requirements.txt
python main.py
```

---

## 📊 ML Model
- Algorithm: Decision Tree Classifier
- Features:
  - hour, day, place_type, popularity
  - area_type, peak_hour, weekend, temp_level
- Target:
  - crowd level (Low / Medium / High)

---

## 📌 Example Output

```bash
Best Time: 7 PM – 10 PM
Crowd: Medium
Risk: Moderate
Advice: Prefer less crowded time slots
```

---

## 🎯 Future Improvements
- Map integration
- Transport recommendations
- UI (Streamlit/Web App)
