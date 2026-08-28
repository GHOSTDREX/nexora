"""Soil Health UI adapter; assessment logic lives only in src.soil_health_engine."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hardware.esp32_client import ESP32Client
from src.soil_health_engine import predict_soil_health

st.set_page_config(page_title="Soil Health | Smart Agriculture AI", page_icon="SH", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"] { font-family:'DM Sans', sans-serif; color:#19302b; }
h1, h2, h3 { font-family:'Space Grotesk', sans-serif; letter-spacing:0; }
.stApp { background:#f5f8f5; }
[data-testid="stSidebar"] { background:#17352d; }
[data-testid="stSidebar"] * { color:#eff8f1; }
.panel { background:#fff; border:1px solid #d9e6df; border-radius:8px; padding:1rem; margin:.6rem 0; }
.badge { display:inline-block; padding:.3rem .65rem; border-radius:999px; background:#dff1e7; color:#176b52; font-weight:700; }
.score { font:700 3rem 'Space Grotesk'; color:#176b52; }
</style>
""", unsafe_allow_html=True)

DEFAULT = {"nitrogen": 35.0, "phosphorus": 30.0, "potassium": 30.0, "soil_moisture": 30.0, "humidity": 60.0, "temperature": 28.0}


def render_result(result: dict) -> None:
    st.markdown(f'<div class="panel"><span class="badge">{result["overall_status"]}</span><div class="score">{result["health_score"]} <small>/ 100</small></div><p>{result["explanation"]}</p></div>', unsafe_allow_html=True)
    columns = st.columns(3)
    for index, (key, factor) in enumerate(result["factors"].items()):
        with columns[index % 3]:
            st.metric(factor["name"], "Not provided" if factor["value"] is None else factor["value"])
            st.caption(factor["status"])
    if result["stress_factors"]:
        st.subheader("Detected issues")
        for factor in result["stress_factors"]:
            st.warning(factor)
    st.subheader("Recommendation")
    st.write(result["recommendation"])
    st.caption(result["disclaimer"])


st.title("Soil Health Analyzer")
st.caption("One deterministic rule engine for manual testing and hardware-ready sensor input.")
mode = st.sidebar.radio("Input mode", ["Manual Test", "ESP32 Live Sensors"])
if mode == "Manual Test":
    with st.form("manual_input"):
        first = st.columns(3)
        nitrogen = first[0].number_input("Nitrogen", min_value=0.0, value=DEFAULT["nitrogen"])
        phosphorus = first[1].number_input("Phosphorus", min_value=0.0, value=DEFAULT["phosphorus"])
        potassium = first[2].number_input("Potassium", min_value=0.0, value=DEFAULT["potassium"])
        second = st.columns(3)
        moisture = second[0].number_input("Soil Moisture", min_value=0.0, max_value=100.0, value=DEFAULT["soil_moisture"])
        humidity = second[1].number_input("Humidity", min_value=0.0, max_value=100.0, value=DEFAULT["humidity"])
        temperature = second[2].number_input("Temperature", value=DEFAULT["temperature"])
        provide_ph = st.checkbox("Provide soil pH")
        soil_ph_input = st.number_input("Soil pH", min_value=0.0, max_value=14.0, value=6.5, disabled=not provide_ph)
        rain = st.checkbox("Rain detected (optional)")
        submitted = st.form_submit_button("Analyze Soil")
    if submitted:
        try:
            values = {"nitrogen": nitrogen, "phosphorus": phosphorus, "potassium": potassium, "soil_moisture": moisture, "humidity": humidity, "temperature": temperature, "rain_detected": rain}
            if provide_ph:
                values["soil_ph"] = soil_ph_input
            render_result(predict_soil_health(**values))
        except ValueError as exc:
            st.error(str(exc))
else:
    st.subheader("ESP32 Sensor Mode")
    endpoint = st.text_input("HTTP sensor endpoint", value="")
    if st.button("Read sensors"):
        try:
            render_result(predict_soil_health(**ESP32Client(endpoint).read()))
        except (ConnectionError, ValueError) as exc:
            st.error(str(exc))
    else:
        st.info("Awaiting sensor data. Configure an endpoint and select Read sensors.")
st.warning("Prototype dataset-derived rules only. Field validation is required before real-world agricultural deployment.")
