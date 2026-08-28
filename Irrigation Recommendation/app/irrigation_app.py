"""
SMART AGRICULTURE AI
Production-Ready IoT + Machine Learning Irrigation Dashboard & AI Agronomist Assistant

Dual Mode System:
1. Live Sensor Mode (ESP32 IoT Telemetry via REST API / Database)
2. Demo Mode (Manual Parameter Simulator)
"""

import os
import sys
import json
import urllib.request
import pandas as pd
import numpy as np
import streamlit as st

# Add workspace directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager
from src.sensor_validator import SensorValidator
from src.feature_mapper import FeatureMapper
from src.irrigation_engine import IrrigationEngine
from src.explanation_engine import ExplanationEngine
from src.agronomist_agent import AgronomistAgent
from src.config import API_BASE_URL, CATEGORICAL_CHOICES, SENSOR_RANGES, FARM_CONFIG_RANGES

# Streamlit Setup
st.set_page_config(
    page_title="Smart Agriculture AI - IoT & Agronomist Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling System
st.markdown("""
<style>
    .main { background-color: #f7faf7; font-family: 'Segoe UI', Roboto, sans-serif; }
    
    .app-header {
        background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 100%);
        color: #ffffff;
        padding: 24px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(27, 67, 50, 0.15);
    }
    .app-title { font-size: 32px; font-weight: 800; margin: 0; color: #ffffff; }
    .app-subtitle { font-size: 16px; font-weight: 400; color: #b7e4c7; margin-top: 4px; }
    
    .mode-banner-live {
        background-color: #e6fcf5; border: 1px solid #20c997; color: #0ca678;
        padding: 10px 16px; border-radius: 8px; font-weight: 700; margin-bottom: 16px;
        display: flex; align-items: center; justify-content: space-between;
    }
    .mode-banner-demo {
        background-color: #fff9db; border: 1px solid #f59f00; color: #d9480f;
        padding: 10px 16px; border-radius: 8px; font-weight: 700; margin-bottom: 16px;
        display: flex; align-items: center; justify-content: space-between;
    }

    .sensor-card {
        background: #ffffff; border: 1px solid #e2ece9; border-radius: 10px;
        padding: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.03); margin-bottom: 12px;
    }
    .sensor-title { font-size: 13px; font-weight: 600; color: #6c757d; }
    .sensor-value { font-size: 26px; font-weight: 800; color: #1b4332; margin: 4px 0; }
    .sensor-meta { font-size: 11px; color: #adb5bd; }
    
    .status-live { background-color: #d3f9d8; color: #2b8a3e; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
    .status-stale { background-color: #ffe3e3; color: #e03131; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }

    .rec-card-high { background: linear-gradient(135deg, #fff5f5 0%, #ffe3e3 100%); border-left: 8px solid #e03131; padding: 24px; border-radius: 10px; }
    .rec-card-medium { background: linear-gradient(135deg, #fff9db 0%, #fff3bf 100%); border-left: 8px solid #f59f00; padding: 24px; border-radius: 10px; }
    .rec-card-low { background: linear-gradient(135deg, #ebfbee 0%, #d3f9d8 100%); border-left: 8px solid #2b8a3e; padding: 24px; border-radius: 10px; }
    
    .rec-val { font-size: 42px; font-weight: 900; line-height: 1; margin: 8px 0; }
    .flow-box { background: #f1f3f5; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 12px; text-align: center; }
</style>
""", unsafe_allow_html=True)


# Singletons
@st.cache_resource
def get_db():
    return DatabaseManager()


@st.cache_resource
def get_engine():
    return IrrigationEngine()


@st.cache_resource
def get_agronomist_agent():
    return AgronomistAgent()


def query_api_predict(payload):
    """Sends prediction request to FastAPI microservice."""
    try:
        url = f"{API_BASE_URL}/api/v1/irrigation/predict"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None


def main():
    db = get_db()
    engine = get_engine()
    agronomist = get_agronomist_agent()

    # Header
    st.markdown("""
    <div class="app-header">
        <h1 class="app-title">Smart Agriculture AI</h1>
        <p class="app-subtitle">IoT + ML Irrigation System & Interactive AI Agronomist Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar: Mode Selector & Farm Config
    st.sidebar.header("🕹️ System Operating Mode")
    app_mode = st.sidebar.radio(
        "Select Operating Mode:",
        ["Live Sensor Mode (ESP32)", "Demo Mode (Manual Input)"]
    )

    farm_id = "FARM_001"
    farm_config = db.get_farm(farm_id) or {
        "farm_id": "FARM_001", "region": "North", "field_area": 2.5,
        "soil_type": "Loamy", "soil_ph": 6.5, "organic_carbon": 0.85,
        "electrical_conductivity": 1.5, "crop_type": "Wheat",
        "crop_growth_stage": "Vegetative", "season": "Rabi", "mulching_used": "No"
    }

    # Mode Banner
    if app_mode == "Live Sensor Mode (ESP32)":
        st.markdown("""
        <div class="mode-banner-live">
            <span>📡 MODE: LIVE SENSOR MODE (ESP32 IoT Telemetry Active)</span>
            <small>Receiving real-world telemetry via API endpoint: /api/v1/sensors/readings</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="mode-banner-demo">
            <span>🧪 MODE: DEMO MODE (Manual Parameter Simulator)</span>
            <small>Hardware simulator active — demo inputs isolated from live telemetry database</small>
        </div>
        """, unsafe_allow_html=True)

    # 1. Farm Overview & Interactive Inputs Section
    if app_mode == "Demo Mode (Manual Input)":
        with st.expander("🚜 Farm Configuration & Soil Test Profile (Insert Actual Values)", expanded=True):
            st.markdown("Customize your farm configuration and soil test metrics below:")
            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1:
                crop_in = st.selectbox("Crop Type", CATEGORICAL_CHOICES["Crop_Type"], index=CATEGORICAL_CHOICES["Crop_Type"].index("Wheat") if "Wheat" in CATEGORICAL_CHOICES["Crop_Type"] else 0)
                stage_in = st.selectbox("Growth Stage", CATEGORICAL_CHOICES["Crop_Growth_Stage"], index=CATEGORICAL_CHOICES["Crop_Growth_Stage"].index("Vegetative") if "Vegetative" in CATEGORICAL_CHOICES["Crop_Growth_Stage"] else 0)
                season_in = st.selectbox("Season", CATEGORICAL_CHOICES["Season"], index=CATEGORICAL_CHOICES["Season"].index("Rabi") if "Rabi" in CATEGORICAL_CHOICES["Season"] else 0)
            with fc2:
                soil_in = st.selectbox("Soil Type", CATEGORICAL_CHOICES["Soil_Type"], index=CATEGORICAL_CHOICES["Soil_Type"].index("Loamy") if "Loamy" in CATEGORICAL_CHOICES["Soil_Type"] else 0)
                mulch_in = st.selectbox("Mulching Used", CATEGORICAL_CHOICES["Mulching_Used"], index=CATEGORICAL_CHOICES["Mulching_Used"].index("No") if "No" in CATEGORICAL_CHOICES["Mulching_Used"] else 0)
                region_in = st.selectbox("Region", CATEGORICAL_CHOICES["Region"], index=CATEGORICAL_CHOICES["Region"].index("North") if "North" in CATEGORICAL_CHOICES["Region"] else 0)
            with fc3:
                area_in = st.number_input("Field Area (ha)", 0.1, 50.0, float(farm_config.get("field_area", 2.5)), 0.5)
                ph_in = st.number_input("Soil pH", 4.0, 9.5, float(farm_config.get("soil_ph", 6.5)), 0.1)
            with fc4:
                oc_in = st.number_input("Organic Carbon (%)", 0.05, 3.0, float(farm_config.get("organic_carbon", 0.85)), 0.05)
                ec_in = st.number_input("Electrical Conductivity (dS/m)", 0.05, 5.0, float(farm_config.get("electrical_conductivity", 1.5)), 0.1)

            farm_config = {
                "farm_id": farm_id,
                "crop_type": crop_in,
                "crop_growth_stage": stage_in,
                "season": season_in,
                "soil_type": soil_in,
                "mulching_used": mulch_in,
                "region": region_in,
                "field_area_hectare": area_in,
                "field_area": area_in,
                "soil_ph": ph_in,
                "organic_carbon": oc_in,
                "electrical_conductivity": ec_in
            }
            st.caption("ℹ️ *Inserted farm configuration and soil test metrics are passed into the ML prediction engine.*")
    else:
        with st.expander("🚜 Farm Configuration & Soil Test Profile", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"**Farm ID:** `{farm_config['farm_id']}`")
                st.markdown(f"**Region:** {farm_config['region']}")
                st.markdown(f"**Field Area:** {farm_config['field_area']} ha")
            with c2:
                st.markdown(f"**Crop:** {farm_config['crop_type']}")
                st.markdown(f"**Growth Stage:** {farm_config['crop_growth_stage']}")
                st.markdown(f"**Season:** {farm_config['season']}")
            with c3:
                st.markdown(f"**Soil Type:** {farm_config['soil_type']}")
                st.markdown(f"**Mulching:** {farm_config['mulching_used']}")
            with c4:
                st.markdown(f"**Soil pH:** {farm_config['soil_ph']}")
                st.markdown(f"**Organic Carbon:** {farm_config['organic_carbon']}%")
                st.markdown(f"**EC:** {farm_config['electrical_conductivity']} dS/m")
            st.caption("ℹ️ *Soil test metrics (pH, Organic Carbon, EC) are derived from farm configuration / periodic soil testing.*")

    # 2. Sensor Telemetry Section (Live vs Demo Mode)
    st.subheader("🌐 Field Sensor Conditions")

    sensor_payload = {}
    is_stale = False
    stale_note = "Live"

    if app_mode == "Live Sensor Mode (ESP32)":
        latest_reading = db.get_latest_sensor_reading(farm_id)
        if latest_reading:
            is_stale, stale_note = SensorValidator.check_staleness(latest_reading.get("timestamp"))
            sensor_payload = {
                "soil_moisture": float(latest_reading["soil_moisture"]),
                "temperature": float(latest_reading["temperature"]),
                "humidity": float(latest_reading["humidity"]),
                "rainfall": float(latest_reading["rainfall"]),
                "sunlight": float(latest_reading["sunlight"]),
                "wind_speed": float(latest_reading["wind_speed"]),
                "timestamp": latest_reading.get("timestamp")
            }
        else:
            st.warning("No ESP32 readings found in database for FARM_001.")
            return

        if is_stale:
            st.warning(f"⚠️ **Sensor Data Stale Warning:** {stale_note} Recommendation operates on last recorded state.")

    else:  # Demo Mode Form
        st.markdown("Insert live sensor measurements for manual simulation:")
        d_col1, d_col2, d_col3, d_col4, d_col5, d_col6 = st.columns(6)
        with d_col1:
            sm_in = st.number_input("Soil Moisture (%)", 0.0, 100.0, 24.5, 0.5)
        with d_col2:
            temp_in = st.number_input("Temp (°C)", -10.0, 60.0, 31.2, 0.5)
        with d_col3:
            hum_in = st.number_input("Humidity (%)", 0.0, 100.0, 55.0, 1.0)
        with d_col4:
            rf_in = st.number_input("Rainfall (mm)", 0.0, 5000.0, 0.0, 5.0)
        with d_col5:
            sun_in = st.number_input("Sunlight (raw/hrs)", 0.0, 100000.0, 850.0, 50.0)
        with d_col6:
            ws_in = st.number_input("Wind (km/h)", 0.0, 150.0, 11.5, 0.5)

        sensor_payload = {
            "soil_moisture": sm_in, "temperature": temp_in, "humidity": hum_in,
            "rainfall": rf_in, "sunlight": sun_in, "wind_speed": ws_in,
            "timestamp": None
        }


    # Render Sensor Telemetry Cards
    sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)

    def render_card(col, title, val, unit, icon, status_tag):
        with col:
            st.markdown(f"""
            <div class="sensor-card">
                <div class="sensor-title">{icon} {title}</div>
                <div class="sensor-value">{val:.1f} <small style="font-size:14px;">{unit}</small></div>
                <div style="margin-top:6px;">Status: <span class="status-{status_tag.lower()}">{status_tag}</span></div>
            </div>
            """, unsafe_allow_html=True)

    status_tag = "STALE" if is_stale else "LIVE"
    render_card(sc1, "Soil Moisture", sensor_payload["soil_moisture"], "%", "🌱", status_tag)
    render_card(sc2, "Temperature", sensor_payload["temperature"], "°C", "🌡", status_tag)
    render_card(sc3, "Humidity", sensor_payload["humidity"], "%", "💧", status_tag)
    render_card(sc4, "Rainfall", sensor_payload["rainfall"], "mm", "🌧", status_tag)
    render_card(sc5, "Sunlight", sensor_payload["sunlight"], "raw", "☀", status_tag)
    render_card(sc6, "Wind Speed", sensor_payload["wind_speed"], "km/h", "💨", status_tag)

    st.markdown("---")

    # 3. Model Inference & Recommendation Pipeline
    predict_payload = {
        "farm_id": farm_id,
        "mode": "Live" if app_mode.startswith("Live") else "Demo",
        "sensor_data": sensor_payload,
        "farm_data": farm_config
    }

    # Query API backend if online, else engine directly
    response = query_api_predict(predict_payload)

    if not response:
        mapped_features = FeatureMapper.map_to_model_features(sensor_payload, farm_config)
        inf = engine.predict(mapped_features)
        agri_supp = ExplanationEngine.generate_agricultural_decision_support(mapped_features, inf["prediction"])
        model_expl = ExplanationEngine.generate_model_explanation(engine)

        response = {
            "status": "success",
            "prediction": inf["prediction"],
            "confidence": inf["confidence"],
            "probabilities": inf["probabilities"],
            "agricultural_decision_support": agri_supp,
            "model_explanation": model_expl
        }

    pred_class = response["prediction"]
    confidence = response["confidence"]
    probabilities = response["probabilities"]
    agri_support = response["agricultural_decision_support"]
    model_expl = response["model_explanation"]

    # Main Tabs: Dashboard vs Interactive AI Agronomist Chat
    tab_dash, tab_agent = st.tabs(["📊 Field Dashboard & ML Inference", "🤖 Interactive AI Agronomist Assistant"])

    with tab_dash:
        r_col1, r_col2 = st.columns([1.1, 0.9])

        with r_col1:
            st.subheader("🎯 Irrigation Recommendation Result")

            if pred_class == "High":
                st.markdown(f"""
                <div class="rec-card-high">
                    <div style="font-size:13px; font-weight:700; color:#495057;">IRRIGATION REQUIREMENT</div>
                    <div class="rec-val" style="color:#e03131;">HIGH</div>
                    <div>Model Confidence: <strong>{confidence:.1f}%</strong></div>
                    <div style="font-size:18px; font-weight:700; color:#c92a2a; margin-top:10px;">
                        💧 Irrigation recommended based on current field conditions.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif pred_class == "Medium":
                st.markdown(f"""
                <div class="rec-card-medium">
                    <div style="font-size:13px; font-weight:700; color:#495057;">IRRIGATION REQUIREMENT</div>
                    <div class="rec-val" style="color:#f59f00;">MEDIUM</div>
                    <div>Model Confidence: <strong>{confidence:.1f}%</strong></div>
                    <div style="font-size:18px; font-weight:700; color:#d9480f; margin-top:10px;">
                        ⚠️ Moderate irrigation requirement. Monitor soil moisture and reassess conditions.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:  # Low
                st.markdown(f"""
                <div class="rec-card-low">
                    <div style="font-size:13px; font-weight:700; color:#495057;">IRRIGATION REQUIREMENT</div>
                    <div class="rec-val" style="color:#2b8a3e;">LOW</div>
                    <div>Model Confidence: <strong>{confidence:.1f}%</strong></div>
                    <div style="font-size:18px; font-weight:700; color:#2b8a3e; margin-top:10px;">
                        ✓ No immediate irrigation recommendation based on current model prediction.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # WHY? Dual Explainability Section
            st.markdown("#### WHY?")

            # Agricultural Decision Support Indicators
            st.markdown("##### 🌾 Agricultural Decision Support")
            for ind in agri_support.get("indicators", []):
                st.markdown(f"- {ind}")
            st.caption("*Rule-based agricultural decision support indicators.*")

            # Model Explanation Section
            st.markdown("##### 🧠 Model Explanation (Decision Tree Feature Importances)")
            if model_expl.get("top_features"):
                for feat_item in model_expl["top_features"][:4]:
                    st.markdown(f"- **{feat_item['Feature']}**: Gini Importance = `{feat_item['Importance']:.4f}`")
            st.caption("*Gini index feature importances extracted from the Decision Tree pipeline.*")

        with r_col2:
            st.subheader("📊 Model Confidence & Class Probabilities")
            st.markdown(f"**Model Confidence:** `{confidence:.1f}%`")

            for cls, prob in probabilities.items():
                prob_pct = prob * 100.0 if prob <= 1.0 else prob
                st.write(f"**{cls}**: {prob_pct:.1f}%")
                st.progress(min(1.0, prob_pct / 100.0))

            st.markdown("---")

            # Historical Sensor Trend Charts
            st.subheader("📈 Live Sensor Historical Trends")
            history = db.get_sensor_history(farm_id, limit=20)

            if history:
                df_hist = pd.DataFrame(history)
                st.markdown("**Soil Moisture (%) Trend:**")
                st.line_chart(df_hist, y="soil_moisture")
                st.markdown("**Temperature (°C) & Humidity (%) Trend:**")
                st.line_chart(df_hist[["temperature", "humidity"]])

    # TAB 2: Interactive AI Agronomist Assistant Chat
    with tab_agent:
        st.subheader("🤖 Interactive AI Agronomist Assistant")
        st.markdown("Ask any questions about your field, water requirements, irrigation timing, or soil health. The AI Agent analyzes your live sensor readings in real-time.")

        # Quick Suggested Prompts
        st.markdown("**Quick Interactive Questions:**")
        p_cols = st.columns(len(agronomist.get_suggested_prompts()))
        selected_prompt = None
        for idx, prompt_text in enumerate(agronomist.get_suggested_prompts()):
            short_label = prompt_text.split("?")[0] + "?"
            if p_cols[idx].button(short_label, key=f"prompt_btn_{idx}"):
                selected_prompt = prompt_text

        # Initialize Chat Messages History
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = [
                {
                    "role": "assistant",
                    "content": f"🌾 Hello! I am your **AI Agronomist**. I have loaded your live sensor data (**{sensor_payload['soil_moisture']}% Moisture**, **{sensor_payload['temperature']}°C Temp**) and farm configuration (**{farm_config['crop_type']}**, **{farm_config['crop_growth_stage']} stage**). How can I assist your farm today?"
                }
            ]

        # Display Chat History
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat Input
        user_input = st.chat_input("Type your farming question here...")
        query_to_process = selected_prompt or user_input

        if query_to_process:
            # Render user message
            st.session_state.chat_messages.append({"role": "user", "content": query_to_process})
            with st.chat_message("user"):
                st.markdown(query_to_process)

            # Process with AI Agronomist Agent
            agent_res = agronomist.process_query(
                user_query=query_to_process,
                sensor_data=sensor_payload,
                farm_data=farm_config,
                prediction_info={"prediction": pred_class, "confidence": confidence}
            )

            assistant_reply = agent_res["response"]
            if agent_res.get("action_bullets"):
                assistant_reply += "\n\n**Action Steps:**\n"
                for b in agent_res["action_bullets"]:
                    assistant_reply += f"- {b}\n"

            st.session_state.chat_messages.append({"role": "assistant", "content": assistant_reply})
            with st.chat_message("assistant"):
                st.markdown(assistant_reply)

    st.markdown("---")

    # 4. Sensor-to-Model Transparency Flowchart
    st.subheader("🔄 How the AI Works (ESP32 Sensor-to-Model Pipeline)")
    st.markdown("""
    <div class="flow-box">
        ESP32 Sensors ➔ Live Field Data ➔ Sensor Validation ➔ Farm Configuration ➔ Feature Mapping ➔ Decision Tree Model ➔ Irrigation Category ➔ Explanation Layer
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 5. Collapsible Model Info & Disclaimer
    with st.expander("ℹ️ Model Information & Operational Disclaimer"):
        st.markdown("""
        **Model Architecture:** Decision Tree Classifier (Pipeline with ColumnTransformer & OneHotEncoder)  
        **Target Variable:** `Irrigation_Need` (`Low` / `Medium` / `High`)  
        **Training Feature Count:** 16  
        **Test-set Accuracy:** **98.38%**
        """)

        metrics_df = pd.DataFrame({
            "Class": ["High", "Low", "Medium"],
            "Precision": [1.00, 0.99, 0.98],
            "Recall": [0.77, 1.00, 0.98],
            "F1-Score": [0.87, 0.99, 0.98]
        })
        st.table(metrics_df)

        st.warning(
            "⚠️ **Operational Disclaimer:** Model performance is based on the available training/test dataset and "
            "may differ under real-world field conditions. Local field validation is recommended before operational deployment."
        )


if __name__ == "__main__":
    main()
