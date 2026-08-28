"""Train and persist the Rice/Sugarcane fertilizer pipeline in this environment."""

from __future__ import annotations

import json
import platform
from datetime import date
from pathlib import Path

import pickle
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "fertilizer_recommendation.csv"
MODEL_PATH = BASE_DIR / "models" / "fertilizer_recommendation_model.pkl"
METADATA_PATH = BASE_DIR / "models" / "fertilizer_model_metadata.json"
FEATURES = ["Crop_Type", "Soil_Type", "Crop_Growth_Stage", "Soil_pH", "Nitrogen_Level", "Phosphorus_Level", "Potassium_Level", "Electrical_Conductivity"]
CATEGORICAL = ["Crop_Type", "Soil_Type", "Crop_Growth_Stage"]
NUMERICAL = ["Soil_pH", "Nitrogen_Level", "Phosphorus_Level", "Potassium_Level", "Electrical_Conductivity"]


def main() -> None:
    frame = pd.read_csv(DATA_PATH)
    frame = frame[frame["Crop_Type"].isin(["Rice", "Sugarcane"])].copy()
    x_train, x_test, y_train, y_test = train_test_split(frame[FEATURES], frame["Recommended_Fertilizer"], test_size=0.2, random_state=42, stratify=frame["Recommended_Fertilizer"])
    preprocessor = ColumnTransformer([("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL), ("numerical", "passthrough", NUMERICAL)])
    pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", DecisionTreeClassifier(class_weight="balanced", max_depth=6, min_samples_leaf=2, min_samples_split=2, random_state=42))])
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    metrics = {"accuracy": round(float(accuracy_score(y_test, predictions)), 4), "balanced_accuracy": round(float(balanced_accuracy_score(y_test, predictions)), 4), "macro_f1": round(float(f1_score(y_test, predictions, average="macro", zero_division=0)), 4), "weighted_f1": round(float(f1_score(y_test, predictions, average="weighted", zero_division=0)), 4)}
    MODEL_PATH.parent.mkdir(exist_ok=True)
    with MODEL_PATH.open("wb") as model_file:
        pickle.dump(pipeline, model_file, protocol=pickle.HIGHEST_PROTOCOL)
    metadata = {"model_name": "Tuned Decision Tree", "algorithm": "DecisionTreeClassifier", "model_type": "Pipeline(ColumnTransformer + OneHotEncoder + DecisionTreeClassifier)", "model_version": "v1.0-prototype", "sklearn_version": sklearn.__version__, "python_version": platform.python_version(), "training_date": date.today().isoformat(), "supported_crops": ["Rice", "Sugarcane"], "feature_list": FEATURES, "target": "Recommended_Fertilizer", "fertilizer_classes": sorted(frame["Recommended_Fertilizer"].unique().tolist()), "training_rows": int(len(frame)), "crop_counts": {str(k): int(v) for k, v in frame["Crop_Type"].value_counts().items()}, "metrics": metrics, "dataset_disclaimer": "Structured or synthetic-like recommendation dataset; held-out metrics are not field accuracy.", "field_validation_status": "Required before real fertilizer application.", "ssp_limitation": "47 SSP records in the Rice + Sugarcane subset; predicted SSP results require additional agronomic validation.", "known_limitations": ["Structured or synthetic-like dataset", "SSP is a low-support class", "Category prediction only; no validated dosage", "Field validation required"]}
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps({"model_path": str(MODEL_PATH), "metrics": metrics, "metadata": metadata}, indent=2))


if __name__ == "__main__":
    main()