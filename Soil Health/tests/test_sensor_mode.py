import unittest

from hardware.sensor_schema import normalize_sensor_payload
from src.soil_health_engine import predict_soil_health

READING = {"nitrogen": 35, "phosphorus": 30, "potassium": 30, "soil_moisture": 30, "humidity": 60, "temperature": 28, "soil_ph": 6.5, "rain_detected": False}


class SensorModeTests(unittest.TestCase):
    def test_manual_and_sensor_results_match(self):
        self.assertEqual(predict_soil_health(**READING), predict_soil_health(**normalize_sensor_payload(READING)))

    def test_invalid_sensor_payload_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_sensor_payload({**READING, "nitrogen": -1})


if __name__ == "__main__":
    unittest.main()
