"""
SMART AGRICULTURE AI
Explanation Engine

Provides dual-layer explainability:
1. Model Explanation (Decision Tree Feature Importances)
2. Agricultural Decision Support (Rule-Based Field Indicators)
"""


class ExplanationEngine:
    @staticmethod
    def generate_agricultural_decision_support(mapped_features, prediction):
        """
        Generates agricultural decision-support indicators based on real input values.
        Clearly labeled as decision-support indicators rather than absolute ML rules.
        """
        indicators = []
        sm = float(mapped_features.get("Soil_Moisture", 30))
        temp = float(mapped_features.get("Temperature_C", 25))
        rf = float(mapped_features.get("Rainfall_mm", 800))
        ws = float(mapped_features.get("Wind_Speed_kmh", 10))
        stage = str(mapped_features.get("Crop_Growth_Stage", "Vegetative"))
        mulch = str(mapped_features.get("Mulching_Used", "No")).strip().capitalize() == "Yes"

        if sm < 20:
            indicators.append("Soil moisture is currently low, indicating increased field water deficit.")
        elif sm > 50:
            indicators.append("Adequate soil moisture retention minimizes immediate water deficit.")

        if temp > 32:
            indicators.append("Temperature is an important decision-support indicator and is currently elevated.")

        if rf < 300:
            indicators.append("Recent cumulative rainfall is limited, indicating low natural water supply.")
        elif rf > 1500:
            indicators.append("Abundant cumulative rainfall reduces additional irrigation necessity.")

        if ws > 15:
            indicators.append("Moderate to high wind speed can increase surface moisture evaporation.")

        if stage in ["Flowering", "Vegetative"]:
            indicators.append(f"The crop is currently in a sensitive growth stage ({stage}).")

        if mulch:
            indicators.append("Mulching helps conserve soil moisture and reduce surface evaporation.")

        if prediction == "Low" and not indicators:
            indicators.append("Current soil and weather conditions indicate relatively lower irrigation demand.")

        return {
            "title": "Agricultural Decision Support Indicators",
            "type": "Rule-based agricultural context",
            "indicators": indicators
        }

    @staticmethod
    def generate_model_explanation(engine_instance):
        """
        Extracts Decision Tree pipeline feature importances for Model Explainability.
        """
        if hasattr(engine_instance, "feature_importance_df") and not engine_instance.feature_importance_df.empty:
            top_features = engine_instance.feature_importance_df.head(6).to_dict(orient="records")
            return {
                "title": "Model Explanation",
                "type": "Decision Tree Feature Importances (Gini Index)",
                "top_features": top_features
            }
        return {
            "title": "Model Explanation",
            "type": "Decision Tree Pipeline",
            "top_features": []
        }
