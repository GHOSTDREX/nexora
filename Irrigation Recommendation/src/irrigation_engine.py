"""
SMART AGRICULTURE AI
Irrigation Engine & Decision-Support System

Integrates with trained Scikit-learn Decision Tree pipeline artifact.
Enforces strict 16-feature input validation, probability extraction,
feature importance calculation, logging, and decision-support reasoning.
"""

import os
import logging
import joblib
import pandas as pd
import numpy as np

# Configure Logging
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("IrrigationEngine")


class IrrigationEngine:
    FEATURES = [
        "Soil_Type",
        "Soil_pH",
        "Soil_Moisture",
        "Organic_Carbon",
        "Electrical_Conductivity",
        "Temperature_C",
        "Humidity",
        "Rainfall_mm",
        "Sunlight_Hours",
        "Wind_Speed_kmh",
        "Crop_Type",
        "Crop_Growth_Stage",
        "Season",
        "Field_Area_hectare",
        "Mulching_Used",
        "Region"
    ]

    CATEGORICAL_OPTIONS = {
        "Soil_Type": ["Clay", "Loamy", "Sandy", "Silt"],
        "Crop_Type": ["Wheat", "Maize", "Cotton", "Rice", "Sugarcane", "Potato"],
        "Crop_Growth_Stage": ["Sowing", "Vegetative", "Flowering", "Harvest"],
        "Season": ["Kharif", "Rabi", "Zaid"],
        "Mulching_Used": ["Yes", "No"],
        "Region": ["North", "South", "East", "West", "Central"]
    }

    NUMERIC_BOUNDS = {
        "Soil_pH": (3.5, 10.5),
        "Soil_Moisture": (0.0, 100.0),
        "Organic_Carbon": (0.0, 10.0),
        "Electrical_Conductivity": (0.0, 20.0),
        "Temperature_C": (-10.0, 60.0),
        "Humidity": (0.0, 100.0),
        "Rainfall_mm": (0.0, 5000.0),
        "Sunlight_Hours": (0.0, 24.0),
        "Wind_Speed_kmh": (0.0, 150.0),
        "Field_Area_hectare": (0.01, 1000.0)
    }

    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(BASE_DIR, "models", "irrigation_prediction_model.pkl")

        if not os.path.exists(model_path):
            err_msg = f"Model artifact file not found at: {model_path}"
            logger.error(err_msg)
            raise FileNotFoundError(err_msg)

        try:
            self.model = joblib.load(model_path)
            logger.info("Decision Tree pipeline model loaded successfully from %s", model_path)
        except Exception as e:
            err_msg = f"Failed to load model artifact: {str(e)}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        self._export_feature_importance()

    def validate_inputs(self, input_dict):
        """Strictly validates presence, types, ranges, and categories for all 16 features."""
        errors = []

        # 1. Missing feature check
        for feat in self.FEATURES:
            if feat not in input_dict or input_dict[feat] is None:
                errors.append(f"Missing required feature: '{feat}'")

        if errors:
            logger.warning("Input validation failed: %s", errors)
            return False, errors

        # 2. Categorical checks
        for cat_feat, valid_choices in self.CATEGORICAL_OPTIONS.items():
            val = str(input_dict.get(cat_feat, "")).strip()
            if val not in valid_choices:
                errors.append(f"Invalid category '{val}' for {cat_feat}. Expected one of: {valid_choices}")

        # 3. Numeric range checks
        for num_feat, (min_val, max_val) in self.NUMERIC_BOUNDS.items():
            try:
                val = float(input_dict[num_feat])
                if val < min_val or val > max_val:
                    errors.append(f"Value {val} for '{num_feat}' is out of valid range [{min_val}, {max_val}].")
            except (ValueError, TypeError):
                errors.append(f"Feature '{num_feat}' must be a valid numeric number.")

        if errors:
            logger.warning("Input validation failed with errors: %s", errors)
            return False, errors

        return True, []

    def predict(self, input_dict):
        """Runs model inference on exactly the 16 trained features."""
        is_valid, errors = self.validate_inputs(input_dict)
        if not is_valid:
            raise ValueError(f"Input Validation Errors: {'; '.join(errors)}")

        # Construct DataFrame preserving exact feature order
        ordered_data = {feat: [input_dict[feat]] for feat in self.FEATURES}
        input_df = pd.DataFrame(ordered_data)

        try:
            raw_prediction = self.model.predict(input_df)[0]
            prediction = str(raw_prediction)

            probabilities_dict = {}
            if hasattr(self.model, "predict_proba"):
                probs = self.model.predict_proba(input_df)[0]
                classes = getattr(self.model, "classes_", ["Low", "Medium", "High"])
                for cls, prob in zip(classes, probs):
                    probabilities_dict[str(cls)] = float(prob)
                confidence = float(max(probs) * 100.0)
            else:
                confidence = 100.0
                probabilities_dict = {prediction: 1.0}

            logger.info("Prediction successful: Class=%s, Confidence=%.2f%%", prediction, confidence)
            return {
                "prediction": prediction,
                "confidence": round(confidence, 1),
                "probabilities": probabilities_dict
            }
        except Exception as e:
            logger.error("Inference failure: %s", str(e))
            raise RuntimeError(f"Model Inference Failed: {str(e)}")

    def _export_feature_importance(self):
        """Extracts feature importances from pipeline and saves outputs/feature_importance.csv."""
        try:
            preprocessor = self.model.named_steps["preprocessor"]
            classifier = self.model.named_steps["classifier"]

            cat_transformer = preprocessor.transformers_[0]
            cat_cols = cat_transformer[2]
            encoder = cat_transformer[1]
            cat_feature_names = list(encoder.get_feature_names_out(cat_cols))

            num_cols = preprocessor.transformers_[1][2]
            all_feature_names = cat_feature_names + list(num_cols)

            importances = classifier.feature_importances_

            df_imp = pd.DataFrame({
                "Feature": all_feature_names,
                "Importance": importances
            }).sort_values(by="Importance", ascending=False)

            outputs_dir = os.path.join(BASE_DIR, "outputs")
            os.makedirs(outputs_dir, exist_ok=True)
            output_csv = os.path.join(outputs_dir, "feature_importance.csv")
            df_imp.to_csv(output_csv, index=False)
            self.feature_importance_df = df_imp
            logger.info("Feature importance exported to %s", output_csv)
        except Exception as e:
            logger.warning("Could not extract feature importance: %s", str(e))
            self.feature_importance_df = pd.DataFrame()

    def get_farm_health_summary(self, input_dict):
        """Qualitative UI interpretation layer for farm conditions."""
        sm = float(input_dict.get("Soil_Moisture", 30))
        temp = float(input_dict.get("Temperature_C", 25))
        rf = float(input_dict.get("Rainfall_mm", 800))
        hum = float(input_dict.get("Humidity", 50))
        ws = float(input_dict.get("Wind_Speed_kmh", 10))

        sm_label = "Low" if sm < 20 else ("Moderate" if sm <= 40 else ("Optimal" if sm <= 60 else "High / Saturated"))
        temp_label = "Cool" if temp < 18 else ("Normal" if temp <= 32 else "Elevated")
        rf_label = "Low" if rf < 500 else ("Moderate" if rf <= 1500 else "High")
        hum_label = "Dry" if hum < 40 else ("Normal" if hum <= 75 else "Humid")
        ws_label = "Calm" if ws < 5 else ("Moderate" if ws <= 15 else "High")

        return {
            "Soil Moisture": (f"{sm:.1f}%", sm_label),
            "Temperature": (f"{temp:.1f} °C", temp_label),
            "Rainfall": (f"{rf:.1f} mm", rf_label),
            "Humidity": (f"{hum:.1f}%", hum_label),
            "Wind Speed": (f"{ws:.1f} km/h", ws_label)
        }

    def get_rule_based_explanation(self, input_dict, prediction):
        """Agricultural rule-based decision-support explanation indicators."""
        indicators = []
        sm = float(input_dict.get("Soil_Moisture", 30))
        temp = float(input_dict.get("Temperature_C", 25))
        rf = float(input_dict.get("Rainfall_mm", 800))
        ws = float(input_dict.get("Wind_Speed_kmh", 10))
        stage = str(input_dict.get("Crop_Growth_Stage", "Vegetative"))
        mulch = str(input_dict.get("Mulching_Used", "No")).strip().capitalize() == "Yes"

        if sm < 25:
            indicators.append("Low soil moisture indicates increased crop water demand.")
        elif sm > 50:
            indicators.append("Adequate soil moisture retention minimizes immediate water deficit.")

        if temp > 32:
            indicators.append("Elevated temperature may accelerate evapotranspiration rates.")

        if rf < 400:
            indicators.append("Recent rainfall conditions indicate limited natural water availability.")
        elif rf > 1500:
            indicators.append("Abundant cumulative rainfall reduces additional irrigation necessity.")

        if ws > 15:
            indicators.append("Moderate to high wind speed can increase surface moisture evaporation.")

        if stage in ["Flowering", "Vegetative"]:
            indicators.append(f"The current crop growth stage ({stage}) is sensitive to moisture availability.")

        if mulch:
            indicators.append("Mulching helps conserve soil moisture and reduce surface evaporation.")

        if prediction == "Low" and not indicators:
            indicators.append("Current soil and weather conditions indicate relatively lower irrigation demand.")

        return indicators