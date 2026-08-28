"""
AgriNova — Crop Recommendation Model Training

Trains a RandomForestClassifier on the classic N/P/K + climate crop
recommendation dataset (2200 rows, 22 crop classes) so the app can return a
real "Recommended Crop + confidence % + alternatives" result (MVP Feature 4),
rather than the rule-based condition-only check the uploaded prototype shipped
with.

Run once (or whenever the dataset changes):
    python -m app.ml.crop_recommendation.train
"""

import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(MODULE_DIR, "crop_recommendation.csv")
MODEL_PATH = os.path.join(MODULE_DIR, "model.joblib")

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET = "label"


def train():
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    test_accuracy = accuracy_score(y_test, model.predict(X_test))
    print(f"Crop recommendation model test accuracy: {test_accuracy:.4f}")

    joblib.dump(model, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    train()
