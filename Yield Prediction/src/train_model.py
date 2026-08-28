"""Yield Prediction — training script.

Fixes applied vs. the originally shipped `final_yield_prediction_model.pkl`
(see notebook/01_yield_prediction_analysis.ipynb for the exploratory work this
builds on):

1. The shipped model's pipeline only used ['crop', 'season', 'area',
   'fertilizer', 'pesticide'] as features. The notebook's own experiments
   (cells 41/46/67) always included 'state' and 'year' too, and every
   evaluated variant in the notebook used the full feature set. The shipped
   artifact silently dropped two of the seven features the analysis actually
   validated. Restored here.
2. 'fertilizer' and 'pesticide' in the source dataset are TOTAL kg used for
   an entire state/district-crop-season-year record (aggregate government
   statistics — area is reported in hectares at district/state scale, median
   ~9,300 ha, not a single smallholder field). Using raw totals as model
   features makes them almost collinear with `area` and means any small farm
   (AgriNova's default is 2.5 ha) sits far outside the training distribution
   for those two columns specifically. Replaced with per-hectare intensity
   (fertilizer_per_ha, pesticide_per_ha), which is scale-invariant and is
   also a quantity a real farmer can plausibly estimate for their own field.
3. Weather features (avg_temp_c, total_rainfall_mm, avg_humidity_percent)
   were merged into the notebook's dataframe but never actually used by any
   trained model there. They are also only available as *annual historical
   averages* (1997-2020) — there's no live equivalent to feed a production
   request for the current year, so using them would require silently
   swapping in an unrelated live weather reading at serve time. Left out
   deliberately; documented here rather than silently ignored like before.
4. Hyperparameters are tuned with time-aware cross-validation (TimeSeriesSplit
   over years) rather than reused ad hoc (the shipped model used
   n_estimators=300 with no recorded search; the notebook's own experiments
   used n_estimators=200/300 interchangeably with no tuning evidence).

Run from the `Yield Prediction/` directory:
    ../backend/venv/Scripts/python.exe src/train_model.py
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, median_absolute_error, r2_score
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "dataset" / "raw" / "crop_yield.csv"
MODEL_DIR = ROOT / "model"
MODEL_PATH = MODEL_DIR / "final_yield_prediction_model.pkl"
METADATA_PATH = MODEL_DIR / "yield_model_metadata.json"

CATEGORICAL_FEATURES = ["crop", "state", "season"]
NUMERIC_FEATURES = ["year", "area", "fertilizer_per_ha", "pesticide_per_ha"]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "yield"
TRAIN_END_YEAR = 2016  # matches the notebook's own chronological split


def _engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # The source CSV pads `season` to a fixed width ('Kharif     ') and has stray
    # whitespace in a few `crop` values ('Coconut ', 'Other  Rabi pulses'). Left
    # uncleaned, a UI sending the visually-correct "Kharif" would be an unseen
    # category to the fitted OneHotEncoder and get silently zeroed out.
    for col in CATEGORICAL_FEATURES:
        df[col] = df[col].str.strip().str.replace(r"\s+", " ", regex=True)
    df["fertilizer_per_ha"] = df["fertilizer"] / df["area"]
    df["pesticide_per_ha"] = df["pesticide"] / df["area"]
    return df


def _build_pipeline(**rf_kwargs) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES),
        ]
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("model", RandomForestRegressor(random_state=42, n_jobs=-1, **rf_kwargs))])


def main() -> None:
    raw = pd.read_csv(DATASET_PATH)
    df = _engineer(raw).sort_values("year").reset_index(drop=True)

    train_df = df[df["year"] <= TRAIN_END_YEAR]
    test_df = df[df["year"] > TRAIN_END_YEAR]

    X_train, y_train = train_df[FEATURES], train_df[TARGET]
    X_test, y_test = test_df[FEATURES], test_df[TARGET]

    print(f"Train: {len(X_train)} rows ({X_train['year'].min()}-{X_train['year'].max()})")
    print(f"Test : {len(X_test)} rows ({X_test['year'].min()}-{X_test['year'].max()})")

    param_distributions = {
        "model__n_estimators": [200, 300, 400, 600],
        "model__max_depth": [None, 12, 20, 30],
        "model__min_samples_leaf": [1, 2, 4],
        "model__max_features": ["sqrt", 0.5, 1.0],
    }

    search = RandomizedSearchCV(
        _build_pipeline(),
        param_distributions=param_distributions,
        n_iter=16,
        scoring="neg_mean_absolute_error",
        cv=TimeSeriesSplit(n_splits=4),
        random_state=42,
        n_jobs=-1,
        verbose=1,
    )
    print("\nTuning hyperparameters (time-aware CV)...")
    search.fit(X_train, y_train)
    print("Best params:", search.best_params_)

    tuned = search.best_estimator_
    y_pred = np.maximum(tuned.predict(X_test), 0)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = r2_score(y_test, y_pred)
    medae = median_absolute_error(y_test, y_pred)

    eval_df = test_df.copy()
    eval_df["predicted_yield"] = y_pred
    eval_df["abs_error"] = (eval_df[TARGET] - eval_df["predicted_yield"]).abs()
    eval_df["rel_error_pct"] = eval_df["abs_error"] / eval_df[TARGET].replace(0, np.nan) * 100
    per_crop = (
        eval_df.groupby("crop")
        .agg(records=("yield", "size"), median_relative_error_pct=("rel_error_pct", "median"))
        .round(2)
    )

    print("\n=== HELD-OUT EVALUATION (2017-2020, unseen at fit time) ===")
    print(f"MAE        : {mae:.4f}")
    print(f"RMSE       : {rmse:.4f}")
    print(f"R2         : {r2:.4f}")
    print(f"Median AE  : {medae:.4f}")
    print(f"Median relative error (all crops): {eval_df['rel_error_pct'].median():.2f}%")

    # Refit best hyperparameters on the FULL dataset (1997-2020) for deployment —
    # the chronological holdout above is only for honest evaluation.
    best_params = {k.replace("model__", ""): v for k, v in search.best_params_.items()}
    final_model = _build_pipeline(**best_params)
    final_model.fit(df[FEATURES], df[TARGET])

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, MODEL_PATH)
    print(f"\nSaved final model -> {MODEL_PATH}")

    metadata = {
        "model_name": "RandomForestRegressor (tuned, time-aware CV)",
        "target": TARGET,
        "target_unit_note": (
            "Yield is production/area in the source dataset's native units per crop "
            "(mostly tonnes/hectare-equivalent, except Coconut which is reported in "
            "nuts/hectare — units are not normalized across crops)."
        ),
        "features": FEATURES,
        "categorical_options": {
            "crop": sorted(df["crop"].unique().tolist()),
            "state": sorted(df["state"].unique().tolist()),
            "season": sorted(df["season"].unique().tolist()),
        },
        "training_rows": int(len(df)),
        "training_year_range": [int(df["year"].min()), int(df["year"].max())],
        "hyperparameters": best_params,
        "held_out_evaluation": {
            "split": f"train<= {TRAIN_END_YEAR}, test > {TRAIN_END_YEAR} (chronological, no temporal leakage)",
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
            "median_absolute_error": round(medae, 4),
            "median_relative_error_pct": round(float(eval_df["rel_error_pct"].median()), 2),
        },
        "per_crop_median_relative_error_pct": per_crop["median_relative_error_pct"].to_dict(),
        "known_limitations": [
            "Source data is state/district-level government aggregate statistics (area "
            "reported in hectares at regional scale, median ~9,300 ha), not per-farm "
            "records. Predictions for a single smallholder field (e.g. 1-5 ha) are an "
            "extrapolation outside the bulk of the training distribution — treat as an "
            "indicative regional outlook by crop/season/state, not a precise field-level "
            "forecast.",
            "Yield units are not normalized across crops (see target_unit_note) — do not "
            "compare raw predicted values across different crops.",
            "Weather (temperature/rainfall/humidity) is not used as a model input; it was "
            "explored in the notebook but only exists as static 1997-2020 historical "
            "annual averages, with no live equivalent for a current-year prediction.",
            "Aggregate R2 is inflated by a small number of very high-yield Coconut "
            "records (reported in nuts/hectare, orders of magnitude above other crops); "
            "median relative error is the more representative accuracy figure.",
        ],
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Saved metadata -> {METADATA_PATH}")


if __name__ == "__main__":
    main()
