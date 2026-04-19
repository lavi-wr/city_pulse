import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
import joblib

df = pd.read_csv("data/clean_crowd_data.csv")

X = df.drop("crowd", axis=1)
buffer = df["crowd"]

X_train, X_test, y_train, y_test = train_test_split(
    X, buffer, test_size=0.2, random_state=42
)

model = DecisionTreeClassifier(max_depth=5)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print(f"\nModel Accuracy: {accuracy * 100:.2f}%")

import os

os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/crowd_model.pkl")
joblib.dump(model, "models/crowd_model.pkl")

print("\nModel saved successfully!")