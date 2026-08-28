import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import fertilizer_engine
from fertilizer_engine import load_model, recommend_fertilizer
from fertilizer_history import recent_recommendations, record_recommendation
from fertilizer_validator import validate_inputs

VALID = {"soil_type": "Loamy", "soil_ph": 6.5, "nitrogen_level": 45, "phosphorus_level": 55, "potassium_level": 70, "electrical_conductivity": 1.2, "crop_growth_stage": "Vegetative"}


class FertilizerTests(unittest.TestCase):
    def test_model_loads_and_has_expected_contract(self):
        model = load_model()
        self.assertEqual(model.feature_names_in_.tolist(), ["Crop_Type", "Soil_Type", "Crop_Growth_Stage", "Soil_pH", "Nitrogen_Level", "Phosphorus_Level", "Potassium_Level", "Electrical_Conductivity"])
        self.assertTrue(hasattr(model, "predict_proba"))

    def test_rice_and_sugarcane_predictions(self):
        for crop in ("Rice", "Sugarcane"):
            result = recommend_fertilizer(crop_type=crop, **VALID)
            self.assertEqual(result["crop"], crop)
            self.assertIn(result["recommended_fertilizer"], load_model().classes_)
            self.assertIn("reason", result)
            self.assertIn("warnings", result)

    def test_invalid_values(self):
        for field, value in (("nitrogen_level", -1), ("soil_ph", 15), ("electrical_conductivity", float("nan"))):
            values = {"crop_type": "Rice", **VALID}
            values[field] = value
            self.assertFalse(validate_inputs(values)["valid"])
        self.assertFalse(validate_inputs({"crop_type": "Wheat", **VALID})["valid"])
        self.assertFalse(validate_inputs({"crop_type": "Rice", **{**VALID, "soil_type": "Unknown"}})["valid"])
        self.assertFalse(validate_inputs({"crop_type": "Rice", **{**VALID, "crop_growth_stage": "Tillering"}})["valid"])
        self.assertFalse(validate_inputs({"crop_type": "Rice", "soil_type": "Loamy"})["valid"])

    def test_out_of_training_range_warns_without_clipping(self):
        values = {"crop_type": "Rice", **{**VALID, "electrical_conductivity": 4.0}}
        result = validate_inputs(values)
        self.assertTrue(result["valid"])
        self.assertTrue(any("outside the model training range" in warning for warning in result["warnings"]))
        self.assertEqual(result["values"]["electrical_conductivity"], 4.0)

    def test_probability_is_not_called_confidence(self):
        result = recommend_fertilizer(crop_type="Rice", **VALID)
        self.assertGreaterEqual(result["model_probability"], 0)
        self.assertLessEqual(result["model_probability"], 100)
        self.assertNotIn("confidence", " ".join(result.keys()).lower())

    def test_ssp_result_has_specific_warning(self):
        class FakeModel:
            classes_ = ["SSP"]

            def predict(self, _row):
                return ["SSP"]

            def predict_proba(self, _row):
                return [[1.0]]

        with patch.object(fertilizer_engine, "MODEL", FakeModel()):
            result = recommend_fertilizer(crop_type="Rice", **VALID)
        self.assertTrue(any("SSP" in warning and "support" in warning for warning in result["warnings"]))

    def test_history_round_trip(self):
        values = {"crop_type": "Rice", **VALID}
        result = recommend_fertilizer(**values)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.db"
            record_recommendation(path, values, result, "Manual Entry")
            rows = recent_recommendations(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["crop"], "Rice")
        self.assertEqual(rows[0]["fertilizer"], result["recommended_fertilizer"])


if __name__ == "__main__":
    unittest.main()