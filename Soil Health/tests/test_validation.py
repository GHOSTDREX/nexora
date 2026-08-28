import unittest

from src.validation import validate_reading

VALID = {"nitrogen": 35, "phosphorus": 30, "potassium": 30, "soil_moisture": 30, "humidity": 60, "temperature": 28}


class ValidationTests(unittest.TestCase):
    def test_valid_payload(self):
        self.assertTrue(validate_reading(VALID)["valid"])

    def test_invalid_values(self):
        result = validate_reading({**VALID, "nitrogen": -20, "humidity": 101, "temperature": "bad"})
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 3)

    def test_optional_values(self):
        result = validate_reading({**VALID, "soil_ph": 6.5, "rain_detected": False})
        self.assertTrue(result["valid"])
        self.assertEqual(result["values"]["soil_ph"], 6.5)


if __name__ == "__main__":
    unittest.main()
