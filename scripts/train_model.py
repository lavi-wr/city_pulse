import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix
)
import joblib

DATA_PATH  = "data/clean_crowd_data.csv"
MODEL_PATH = "models/crowd_model.pkl"

FEATURE_COLS = ["hour", "day", "place_type", "popularity",
                "area_type", "peak_hour", "weekend", "temp_level"]
TARGET_COL   = "crowd"
LABEL_NAMES  = ["Low", "Medium", "High"]


def _header(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")

_header("Loading data")
df = pd.read_csv(DATA_PATH)
print(f"  Shape : {df.shape[0]:,} rows × {df.shape[1]} columns")

X = df[FEATURE_COLS]
y = df[TARGET_COL]

_header("Train / Test split")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"  Training samples : {len(X_train):,}")
print(f"  Test samples     : {len(X_test):,}")

_header("Training Decision Tree (max_depth=8)")
model = DecisionTreeClassifier(max_depth=8, class_weight="balanced")
model.fit(X_train, y_train)
print("  ✅ Training complete")

_header("Evaluation")
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n  Accuracy : {accuracy * 100:.2f}%")

print("\n  Classification Report:")
print(classification_report(y_test, y_pred, target_names=LABEL_NAMES))

print("  Confusion Matrix (rows=actual, cols=predicted):")
cm = confusion_matrix(y_test, y_pred)
cm_df = pd.DataFrame(cm, index=LABEL_NAMES, columns=LABEL_NAMES)
print(cm_df.to_string())

_header("Feature Importances")
importances = sorted(
    zip(FEATURE_COLS, model.feature_importances_),
    key=lambda x: x[1], reverse=True
)
for feat, imp in importances:
    bar = "█" * int(imp * 40)
    print(f"  {feat:<15}: {imp:.4f}  {bar}")

_header("Saving model")
os.makedirs("models", exist_ok=True)
joblib.dump(model, MODEL_PATH)
print(f"  Saved to : {MODEL_PATH}")
print("\n✅ Training complete!")