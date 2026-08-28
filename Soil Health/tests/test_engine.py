import unittest

from src.soil_health_engine import predict_soil_health

BASE = {"nitrogen": 35, "phosphorus": 30, "potassium": 30, "soil_moisture": 30, "humidity": 60, "temperature": 28, "soil_ph": 6.5, "rain_detected": False}


class EngineTests(unittest.TestCase):
    def test_regression_case_is_healthy(self):
        result = predict_soil_health(**BASE)
        self.assertEqual(result["overall_status"], "Healthy")
        self.assertEqual(result["health_score"], 100)
        self.assertEqual(result["stress_factors"], [])
        for name in ("nitrogen", "phosphorus", "potassium", "soil_moisture", "humidity", "temperature", "soil_ph"):
            self.assertEqual(result["factors"][name]["status"], "Healthy")

    def test_each_required_stress_case(self):
        cases = (("nitrogen", 20, "Nitrogen"), ("phosphorus", 20, "Phosphorus"), ("potassium", 20, "Potassium"), ("soil_moisture", 15, "Soil Moisture"), ("humidity", 10, "Humidity"), ("humidity", 90, "Humidity"), ("temperature", 5, "Temperature"), ("temperature", 40, "Temperature"), ("soil_ph", 5.5, "Soil pH"), ("soil_ph", 7.1, "Soil pH"))
        for field, value, expected in cases:
            with self.subTest(field=field, value=value):
                result = predict_soil_health(**{**BASE, field: value})
                self.assertIn(expected, result["stress_factors"])
                self.assertEqual(result["factors"][field]["status"], "Moderate Stress")

    def test_multiple_stress_factors_are_preserved(self):
        result = predict_soil_health(**{**BASE, "nitrogen": 20, "phosphorus": 20, "potassium": 20, "soil_moisture": 15, "soil_ph": 5.5, "humidity": 95, "temperature": 45})
        self.assertEqual(result["stress_factors"], ["Nitrogen", "Phosphorus", "Potassium", "Soil Moisture", "Humidity", "Temperature", "Soil pH"])
        self.assertEqual(result["health_score"], 0)

    def test_threshold_boundaries(self):
        for field, below, at, above in (("nitrogen", 29.9, 30.0, 30.1), ("phosphorus", 24.9, 25.0, 25.1), ("potassium", 24.9, 25.0, 25.1), ("soil_moisture", 24.9, 25.0, 25.1)):
            with self.subTest(field=field):
                self.assertEqual(predict_soil_health(**{**BASE, field: below})["factors"][field]["status"], "Moderate Stress")
                self.assertEqual(predict_soil_health(**{**BASE, field: at})["factors"][field]["status"], "Healthy")
                self.assertEqual(predict_soil_health(**{**BASE, field: above})["factors"][field]["status"], "Healthy")
        for value, expected in ((5.5, "Moderate Stress"), (6.0, "Moderate Stress"), (6.1, "Healthy"), (7.0, "Healthy"), (7.1, "Moderate Stress")):
            with self.subTest(soil_ph=value):
                self.assertEqual(predict_soil_health(**{**BASE, "soil_ph": value})["factors"]["soil_ph"]["status"], expected)
        for value, expected in ((14.9, "Moderate Stress"), (15.0, "Healthy"), (35.0, "Healthy"), (35.1, "Moderate Stress")):
            with self.subTest(temperature=value):
                self.assertEqual(predict_soil_health(**{**BASE, "temperature": value})["factors"]["temperature"]["status"], expected)
        for value, expected in ((29.9, "Moderate Stress"), (30.0, "Healthy"), (85.0, "Healthy"), (85.1, "Moderate Stress")):
            with self.subTest(humidity=value):
                self.assertEqual(predict_soil_health(**{**BASE, "humidity": value})["factors"]["humidity"]["status"], expected)

    def test_missing_ph_is_not_zero(self):
        result = predict_soil_health(**{key: value for key, value in BASE.items() if key not in {"soil_ph", "rain_detected"}})
        self.assertIsNone(result["factors"]["soil_ph"]["value"])
        self.assertEqual(result["factors"]["soil_ph"]["status"], "Not evaluated")
        self.assertNotIn("Soil pH", result["stress_factors"])


if __name__ == "__main__":
    unittest.main()
