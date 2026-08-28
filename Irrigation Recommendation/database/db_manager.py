"""
SMART AGRICULTURE AI
Database Manager (SQLite)
"""

import os
import sqlite3
from datetime import datetime, timedelta, timezone
try:
    from src.config import DB_PATH
except ImportError:
    from config import DB_PATH


class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Farms Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS farms (
                farm_id TEXT PRIMARY KEY,
                region TEXT NOT NULL,
                field_area REAL NOT NULL,
                soil_type TEXT NOT NULL,
                soil_ph REAL NOT NULL,
                organic_carbon REAL NOT NULL,
                electrical_conductivity REAL NOT NULL,
                crop_type TEXT NOT NULL,
                crop_growth_stage TEXT NOT NULL,
                season TEXT NOT NULL,
                mulching_used TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # 2. Sensor Readings Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                soil_moisture REAL NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                rainfall REAL NOT NULL,
                sunlight REAL NOT NULL,
                wind_speed REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (farm_id) REFERENCES farms(farm_id)
            );
            """)

            # 3. Irrigation Predictions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS irrigation_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                prediction TEXT NOT NULL,
                confidence REAL NOT NULL,
                low_probability REAL NOT NULL,
                medium_probability REAL NOT NULL,
                high_probability REAL NOT NULL,
                mode TEXT NOT NULL,
                FOREIGN KEY (farm_id) REFERENCES farms(farm_id)
            );
            """)

            conn.commit()

        # Seed initial default farm if not exists
        self.seed_default_farm()

    def seed_default_farm(self):
        now_str = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT farm_id FROM farms WHERE farm_id = 'FARM_001'")
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO farms (
                    farm_id, region, field_area, soil_type, soil_ph, organic_carbon,
                    electrical_conductivity, crop_type, crop_growth_stage, season,
                    mulching_used, updated_at
                ) VALUES (
                    'FARM_001', 'North', 2.5, 'Loamy', 6.5, 0.85,
                    1.5, 'Wheat', 'Vegetative', 'Rabi', 'No', ?
                );
                """, (now_str,))

                # Seed sample historical readings for FARM_001
                base_time = datetime.now(timezone.utc)
                sample_readings = [
                    (-60, 32.5, 24.0, 58.0, 0.0, 650.0, 8.5),
                    (-45, 30.0, 25.5, 55.0, 0.0, 720.0, 9.2),
                    (-30, 28.0, 27.0, 52.0, 0.0, 800.0, 10.5),
                    (-15, 26.5, 28.5, 50.0, 0.0, 850.0, 11.2),
                    (0, 25.0, 29.5, 48.0, 0.0, 910.0, 12.0)
                ]
                for offset_min, sm, temp, hum, rf, sun, ws in sample_readings:
                    t_str = (base_time + timedelta(minutes=offset_min)).isoformat()
                    cursor.execute("""
                    INSERT INTO sensor_readings (
                        farm_id, device_id, timestamp, soil_moisture, temperature,
                        humidity, rainfall, sunlight, wind_speed, status
                    ) VALUES (
                        'FARM_001', 'ESP32_FIELD_01', ?, ?, ?, ?, ?, ?, ?, 'LIVE'
                    );
                    """, (t_str, sm, temp, hum, rf, sun, ws))

                conn.commit()

    def get_farm(self, farm_id="FARM_001"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM farms WHERE farm_id = ?", (farm_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def upsert_farm(self, farm_dict):
        now_str = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO farms (
                farm_id, region, field_area, soil_type, soil_ph, organic_carbon,
                electrical_conductivity, crop_type, crop_growth_stage, season,
                mulching_used, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(farm_id) DO UPDATE SET
                region=excluded.region,
                field_area=excluded.field_area,
                soil_type=excluded.soil_type,
                soil_ph=excluded.soil_ph,
                organic_carbon=excluded.organic_carbon,
                electrical_conductivity=excluded.electrical_conductivity,
                crop_type=excluded.crop_type,
                crop_growth_stage=excluded.crop_growth_stage,
                season=excluded.season,
                mulching_used=excluded.mulching_used,
                updated_at=excluded.updated_at;
            """, (
                farm_dict.get("farm_id", "FARM_001"),
                farm_dict.get("region", "North"),
                float(farm_dict.get("field_area", 2.5)),
                farm_dict.get("soil_type", "Loamy"),
                float(farm_dict.get("soil_ph", 6.5)),
                float(farm_dict.get("organic_carbon", 0.85)),
                float(farm_dict.get("electrical_conductivity", 1.5)),
                farm_dict.get("crop_type", "Wheat"),
                farm_dict.get("crop_growth_stage", "Vegetative"),
                farm_dict.get("season", "Rabi"),
                farm_dict.get("mulching_used", "No"),
                now_str
            ))
            conn.commit()

    def insert_sensor_reading(self, reading_dict):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sensor_readings (
                farm_id, device_id, timestamp, soil_moisture, temperature,
                humidity, rainfall, sunlight, wind_speed, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                reading_dict.get("farm_id", "FARM_001"),
                reading_dict.get("device_id", "ESP32_FIELD_01"),
                reading_dict.get("timestamp", datetime.now(timezone.utc).isoformat()),
                float(reading_dict.get("soil_moisture", 25.0)),
                float(reading_dict.get("temperature", 25.0)),
                float(reading_dict.get("humidity", 50.0)),
                float(reading_dict.get("rainfall", 0.0)),
                float(reading_dict.get("sunlight", 0.0)),
                float(reading_dict.get("wind_speed", 10.0)),
                reading_dict.get("status", "LIVE")
            ))
            conn.commit()

    def get_latest_sensor_reading(self, farm_id="FARM_001"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM sensor_readings
            WHERE farm_id = ?
            ORDER BY id DESC LIMIT 1;
            """, (farm_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_sensor_history(self, farm_id="FARM_001", limit=30):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM sensor_readings
            WHERE farm_id = ?
            ORDER BY id DESC LIMIT ?;
            """, (farm_id, limit))
            rows = cursor.fetchall()
            return [dict(r) for r in reversed(rows)]

    def insert_prediction(self, pred_dict):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            probs = pred_dict.get("probabilities", {})
            cursor.execute("""
            INSERT INTO irrigation_predictions (
                farm_id, timestamp, prediction, confidence,
                low_probability, medium_probability, high_probability, mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                pred_dict.get("farm_id", "FARM_001"),
                datetime.now(timezone.utc).isoformat(),
                pred_dict.get("prediction", "Low"),
                float(pred_dict.get("confidence", 100.0)),
                float(probs.get("Low", 0.0)),
                float(probs.get("Medium", 0.0)),
                float(probs.get("High", 0.0)),
                pred_dict.get("mode", "Live")
            ))
            conn.commit()
