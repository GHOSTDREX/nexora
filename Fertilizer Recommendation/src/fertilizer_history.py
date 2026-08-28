"""Small local SQLite audit log with no personal information."""

from pathlib import Path
import sqlite3
from typing import Any


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, crop TEXT,
        input_mode TEXT, soil_type TEXT, growth_stage TEXT, nitrogen REAL,
        phosphorus REAL, potassium REAL, soil_ph REAL, electrical_conductivity REAL,
        fertilizer TEXT, model_probability REAL, warning_status TEXT)""")
    connection.commit()
    return connection


def record_recommendation(path: Path, values: dict[str, Any], result: dict[str, Any], input_mode: str) -> None:
    connection = _connect(path)
    try:
        connection.execute("""INSERT INTO recommendations
            (timestamp, crop, input_mode, soil_type, growth_stage, nitrogen, phosphorus,
             potassium, soil_ph, electrical_conductivity, fertilizer, model_probability, warning_status)
            VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            result["crop"], input_mode, values["soil_type"], values["crop_growth_stage"], values["nitrogen_level"], values["phosphorus_level"], values["potassium_level"], values["soil_ph"], values["electrical_conductivity"], result["recommended_fertilizer"], result["model_probability"], "; ".join(result["warnings"])))
        connection.commit()
    finally:
        connection.close()


def recent_recommendations(path: Path, limit: int = 10) -> list[dict[str, Any]]:
    connection = _connect(path)
    try:
        return [dict(row) for row in connection.execute("SELECT * FROM recommendations ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
    finally:
        connection.close()