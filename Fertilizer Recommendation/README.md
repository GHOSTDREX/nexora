# Fertilizer Recommendation

This module is a prototype AI-assisted fertilizer decision-support system for **one selected crop at a time**: Rice or Sugarcane. It predicts a fertilizer category, not a scientifically validated dose.

## Run from the project root

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python "Fertilizer Recommendation\src\train_model.py"
python -m unittest discover -s "Fertilizer Recommendation\tests" -v
streamlit run "Fertilizer Recommendation\app\fertilizer_app.py"
```

The Streamlit app normally opens at `http://localhost:8501`.

## Inputs and modes

Manual Entry is the default. Demo Sensor Data is simulated and explicitly labeled. Live ESP32 currently reports that the device is not connected; it does not invent missing N/P/K, pH, or EC values. N/P/K values should be treated as manual or soil-test inputs unless a validated instrument supplies them.

The model accepts the dataset's generic stages: Sowing, Vegetative, Flowering, and Harvest. No unvalidated crop-specific stage mapping is applied.

## Model

The persisted artifact is a scikit-learn Pipeline containing a ColumnTransformer, OneHotEncoder with `handle_unknown="ignore"`, and a balanced DecisionTreeClassifier (`max_depth=6`, `min_samples_leaf=2`, `min_samples_split=2`, `random_state=42`). Training uses only the Rice and Sugarcane subset and the documented eight features. Metadata is stored beside the model.

Nutrient and pH labels are **dataset-derived prototype interpretation thresholds**, not agronomic thresholds. The dataset is structured or synthetic-like. Held-out classification metrics are useful for this prototype dataset only and do not represent field accuracy. SSP has limited support and receives an additional warning.

## Outputs and audit history

Results include fertilizer category, model probability, nutrient status, a conservative dataset-based explanation, and warnings. Model probability is not certainty. No fertilizer quantity, kg/ha, application schedule, or product conversion is invented. Recommendations are logged locally in `data/fertilizer_history.db` without personal information.

## Structure

`src/fertilizer_engine.py` is the UI-independent service. `fertilizer_validator.py`, `fertilizer_explanation_engine.py`, `fertilizer_history.py`, and `model_info.py` provide the supporting boundaries. `app/fertilizer_app.py` is the Streamlit client demo. `src/train_model.py` recreates the model artifact in the active environment. `tests/` contains automated contract and validation tests.

## Disclaimer

This is prototype decision-support based on the current training dataset. It is not a certified agronomic prescription. Field testing, soil-test interpretation, local agronomic guidance, and approval are required before real fertilizer application.