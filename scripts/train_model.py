import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
import joblib

# -------------------------------
# 1. LOAD DATA
# -------------------------------
df = pd.read_csv("data/clean_crowd_data.csv")

# -------------------------------
# 2. SPLIT FEATURES & TARGET
# -------------------------------
X = df.drop("crowd", axis=1)
y = df["crowd"]

# -------------------------------
# 3. TRAIN-TEST SPLIT
# -------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -------------------------------
# 4. TRAIN MODEL
# -------------------------------
model = DecisionTreeClassifier(max_depth=5)
model.fit(X_train, y_train)

# -------------------------------
# 5. PREDICT & EVALUATE
# -------------------------------
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print(f"\nModel Accuracy: {accuracy * 100:.2f}%")

# -------------------------------
# 6. SAVE MODEL
# -------------------------------
import os

# create models folder if not exists
os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/crowd_model.pkl")
joblib.dump(model, "models/crowd_model.pkl")

print("\nModel saved successfully!")