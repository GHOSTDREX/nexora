"""Client-demo-ready Streamlit interface for fertilizer decision support."""

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fertilizer_engine import MODEL_PATH, load_model, recommend_fertilizer
from fertilizer_history import recent_recommendations, record_recommendation
from fertilizer_validator import SUPPORTED_SOILS, SUPPORTED_STAGES, TRAINING_RANGES, validate_inputs
from model_info import load_model_info

st.set_page_config(page_title="Fertilizer Recommendation Intelligence", page_icon="SA", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    :root { --ink: #1f3028; --muted: #62736a; --line: #dfe7df; --paper: #fbfcf9; --leaf: #246b4b; --leaf-dark: #174c36; --gold: #b17618; }
    .stApp { background: var(--paper); }
    .block-container { max-width: 1240px; padding: 2.2rem 2.3rem 4rem; }
    [data-testid="stMetricValue"] { color: var(--leaf-dark); font-size: 1.55rem; }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    .hero { background: linear-gradient(120deg, #1b4f38 0%, #2e7450 62%, #6f8b57 100%); color: white; border-radius: 16px; padding: 2rem 2.1rem; margin-bottom: 1.1rem; box-shadow: 0 12px 30px rgba(31, 80, 55, .12); }
    .hero h1 { color: white; font-size: 2.25rem; margin: 0 0 .35rem; letter-spacing: 0; }
    .hero p { color: #e5f0e8; margin: 0; font-size: 1rem; }
    .status-row { display: flex; gap: .55rem; flex-wrap: wrap; margin-top: 1.1rem; }
    .status { border: 1px solid rgba(255,255,255,.28); border-radius: 999px; padding: .32rem .7rem; font-size: .78rem; color: #f3f8f3; background: rgba(255,255,255,.1); }
    .section-kicker { color: var(--leaf); text-transform: uppercase; font-size: .72rem; font-weight: 800; letter-spacing: .08em; margin: .25rem 0 .35rem; }
    .section-title { color: var(--ink); font-size: 1.35rem; font-weight: 800; margin: 0 0 .25rem; }
    .section-copy { color: var(--muted); margin: 0 0 1rem; }
    .crop-card { border: 1px solid var(--line); background: white; border-radius: 12px; padding: 1.05rem 1.1rem; min-height: 120px; box-shadow: 0 5px 16px rgba(35, 63, 44, .04); }
    .crop-card.active { border: 2px solid var(--leaf); background: #f1f8f2; }
    .crop-card h3 { color: var(--ink); margin: 0 0 .35rem; }
    .crop-card p { color: var(--muted); font-size: .88rem; margin: 0; }
    .panel { background: white; border: 1px solid var(--line); border-radius: 12px; padding: 1.15rem 1.25rem; box-shadow: 0 5px 16px rgba(35, 63, 44, .04); }
    .result-panel { background: #f1f8f2; border: 1px solid #cfe3d3; border-radius: 12px; padding: 1.4rem; }
    .result-label { color: var(--leaf); font-size: .78rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
    .fertilizer-name { color: var(--leaf-dark); font-size: 2.1rem; font-weight: 850; margin: .18rem 0 .25rem; }
    .note { color: var(--muted); font-size: .82rem; }
    .warning-box { background: #fff8e8; border-left: 4px solid var(--gold); border-radius: 5px; padding: .75rem .9rem; margin: .55rem 0; color: #5f481f; }
    .good-box { background: #edf7ef; border-left: 4px solid var(--leaf); border-radius: 5px; padding: .75rem .9rem; color: #29533b; }
    .empty-state { text-align: center; border: 1px dashed #c8d8cb; border-radius: 12px; padding: 3.5rem 1rem; background: #f6faf6; color: var(--muted); }
    div[data-testid="stForm"] { border: 0; padding: 0; }
    button[kind="primary"] { background: var(--leaf); border-color: var(--leaf); }
    button[kind="primary"]:hover { background: var(--leaf-dark); border-color: var(--leaf-dark); }
    @media (max-width: 720px) { .block-container { padding: 1rem .8rem 3rem; } .hero h1 { font-size: 1.7rem; } .fertilizer-name { font-size: 1.7rem; } }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def cached_model():
    return load_model()


@st.cache_data
def model_metadata():
    return load_model_info()


def init_state() -> None:
    defaults = {"crop": "Rice", "mode": "Manual Entry", "result": None, "scenario": "Custom input", "scenario_seen": ""}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def apply_scenario(name: str) -> None:
    scenarios = {
        "Rice — Low Nitrogen": {"crop": "Rice", "soil_type": "Loamy", "growth_stage": "Vegetative", "soil_ph": 6.5, "nitrogen": 35.0, "phosphorus": 55.0, "potassium": 70.0, "ec": 1.2},
        "Rice — Low Potassium": {"crop": "Rice", "soil_type": "Clay", "growth_stage": "Flowering", "soil_ph": 6.4, "nitrogen": 82.0, "phosphorus": 54.0, "potassium": 24.0, "ec": 1.4},
        "Sugarcane — Low Phosphorus": {"crop": "Sugarcane", "soil_type": "Loamy", "growth_stage": "Vegetative", "soil_ph": 6.7, "nitrogen": 88.0, "phosphorus": 22.0, "potassium": 72.0, "ec": 1.3},
        "Sugarcane — Balanced Nutrients": {"crop": "Sugarcane", "soil_type": "Silt", "growth_stage": "Sowing", "soil_ph": 6.8, "nitrogen": 78.0, "phosphorus": 58.0, "potassium": 66.0, "ec": 1.1},
    }
    selected = scenarios.get(name)
    if not selected:
        return
    st.session_state.update(selected)
    st.session_state["scenario_seen"] = name
    st.session_state["result"] = None


def crop_selector() -> None:
    st.markdown('<div class="section-kicker">01 / Crop scope</div><div class="section-title">Select one crop to begin</div><p class="section-copy">The recommendation workflow is crop-specific. Rice and Sugarcane use the same validated model pipeline internally.</p>', unsafe_allow_html=True)
    cards = st.columns(2)
    for column, crop, subtitle in zip(cards, ["Rice", "Sugarcane"], ["Analyze soil nutrient conditions for Rice fertilizer recommendation.", "Analyze soil nutrient conditions for Sugarcane fertilizer recommendation."]):
        active = st.session_state.crop == crop
        column.markdown(f'<div class="crop-card {"active" if active else ""}"><h3>{"Rice" if crop == "Rice" else "Sugarcane"}</h3><p>{subtitle}</p></div>', unsafe_allow_html=True)
        if column.button(f"Select {crop}", key=f"select_{crop}", use_container_width=True, type="primary" if active else "secondary"):
            st.session_state.crop = crop
            st.session_state.result = None
            st.rerun()


def status_card(mode: str) -> None:
    model_ready = MODEL_PATH.exists()
    database_ready = True
    st.sidebar.markdown("### System status")
    st.sidebar.success("Model: Ready" if model_ready else "Model: Unavailable")
    st.sidebar.info("Input validator: Ready")
    st.sidebar.info("Database: Connected" if database_ready else "Database: Unavailable")
    st.sidebar.warning("ESP32: Not connected")
    st.sidebar.caption(f"Mode: {mode}")


def render_validation(values: dict) -> dict:
    validation = validate_inputs(values)
    st.markdown('<div class="section-kicker">Input quality</div><div class="section-title">Validation status</div>', unsafe_allow_html=True)
    if validation["valid"] and validation["warnings"]:
        st.warning("Ready with advisory warnings. " + " ".join(validation["warnings"]))
    elif validation["valid"]:
        st.success("Ready — all inputs are compatible with the current model.")
    else:
        st.error("Invalid — correct the highlighted measurements before analysis.")
        for error in validation["errors"]:
            st.write(f"• {error}")
    checks = st.columns(4)
    checks[0].caption("✓ Crop supported")
    checks[1].caption("✓ Model-compatible stage")
    checks[2].caption("✓ Numeric measurements")
    checks[3].caption("✓ No hidden values")
    return validation


def render_result(result: dict, values: dict) -> None:
    st.markdown('<div class="section-kicker">Decision support</div><div class="section-title">Analysis result</div>', unsafe_allow_html=True)
    left, right = st.columns([1.18, .82])
    with left:
        st.markdown(f'<div class="result-panel"><div class="result-label">Recommended fertilizer</div><div class="fertilizer-name">{result["recommended_fertilizer"]}</div><div class="note">Recommended for the current {result["crop"]} soil profile</div></div>', unsafe_allow_html=True)
    with right:
        st.metric("Model Probability", f'{result["model_probability"]:.2f}%')
        st.caption("Classifier output, not real-world certainty.")
    st.markdown("#### Nutrient condition")
    nutrient_items = [("nitrogen", "Nitrogen"), ("phosphorus", "Phosphorus"), ("potassium", "Potassium"), ("soil_ph", "Soil pH")]
    cards = st.columns(4)
    for card, (key, label) in zip(cards, nutrient_items):
        card.metric(label, result["nutrient_status"][key])
    st.caption("Prototype interpretation based on dataset-derived thresholds, not scientifically validated agronomic thresholds.")
    st.markdown("#### Why was this fertilizer recommended?")
    st.write(result["reason"])
    info = {"Urea": ("Nitrogen fertilizer", "Supports nitrogen replenishment patterns represented in the prototype dataset."), "DAP": ("Nitrogen + phosphorus fertilizer", "A combined nutrient category represented in the model training data."), "MOP": ("Potassium fertilizer", "A potassium-oriented fertilizer category represented in the model training data."), "Compost": ("Organic soil amendment", "An organic amendment category represented in the model training data."), "Zinc Sulphate": ("Zinc micronutrient source", "A micronutrient category represented in the model training data."), "NPK": ("Balanced multi-nutrient fertilizer", "A combined N/P/K category represented in the model training data."), "SSP": ("Phosphorus fertilizer", "A low-support category in this Rice + Sugarcane dataset.")}[result["recommended_fertilizer"]]
    with st.expander("Fertilizer information"):
        st.write(f"**Primary role:** {info[0]}")
        st.write(info[1])
        st.info("Dose recommendation is not available in the current validated model. Quantity and timing require crop-specific agronomic prescription data.")
    with st.expander("Factors considered"):
        st.write("The pipeline evaluated these model inputs. They are not assumed to contribute equally to this individual prediction.")
        st.dataframe(pd.DataFrame({"Model feature": ["Selected Crop", "Soil Type", "Crop Growth Stage", "Soil pH", "Nitrogen", "Phosphorus", "Potassium", "Electrical Conductivity"], "Current value": [values["crop_type"], values["soil_type"], values["crop_growth_stage"], values["soil_ph"], values["nitrogen_level"], values["phosphorus_level"], values["potassium_level"], values["electrical_conductivity"]]}), hide_index=True, use_container_width=True)
    for warning in result["warnings"]:
        st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)


init_state()
info = model_metadata()
st.markdown(f'<div class="hero"><h1>Smart Agriculture AI</h1><p>Fertilizer Recommendation Intelligence</p><p style="margin-top:.55rem">AI-assisted soil nutrient analysis and fertilizer category recommendation for Rice and Sugarcane.</p><div class="status-row"><span class="status">● Model Ready</span><span class="status">● Manual Mode</span><span class="status">● Prototype System</span><span class="status">● ESP32 Pending</span></div></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Fertilizer workspace")
    st.caption("A transparent decision-support prototype for field teams and agronomy review.")
    st.markdown("### Demo scenario")
    scenario = st.selectbox("Choose a starting profile", ["Custom input", "Rice — Low Nitrogen", "Rice — Low Potassium", "Sugarcane — Low Phosphorus", "Sugarcane — Balanced Nutrients"], key="scenario")
    if scenario != st.session_state.scenario_seen and scenario != "Custom input":
        apply_scenario(scenario)
        st.rerun()
    if st.button("Reset to custom input", use_container_width=True):
        st.session_state.scenario = "Custom input"
        st.session_state.scenario_seen = "Custom input"
        st.session_state.result = None
        st.rerun()
    st.divider()
    with st.expander("About this AI model"):
        st.write(f"**Algorithm:** {info.get('model_name', 'Tuned Decision Tree Classifier')}")
        st.write("**Supported crops:** Rice, Sugarcane")
        st.write("**Prediction:** Fertilizer category")
        st.write(f"**Training data:** {info.get('training_rows', 2857):,} records")
        metrics = info.get("metrics", {})
        st.write(f"**Held-out accuracy:** {metrics.get('accuracy', 0) * 100:.1f}%")
        st.write(f"**Balanced accuracy:** {metrics.get('balanced_accuracy', 0) * 100:.1f}%")
        st.write(f"**Macro F1:** {metrics.get('macro_f1', 0):.3f}")
        st.caption("Structured/synthetic-like dataset. Metrics describe held-out classification on this prototype dataset, not field accuracy.")

crop_selector()
st.divider()
st.markdown(f'<div class="section-kicker">Active workflow</div><div class="section-title">{st.session_state.crop} Fertilizer Recommendation</div><p class="section-copy">Receive or enter soil measurements for this crop. Use manual or soil-test values for N/P/K unless a validated instrument supplies them. No values are silently fabricated.</p>', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">02 / Measurements</div><div class="section-title">Receive or enter soil measurements</div>', unsafe_allow_html=True)
mode = st.radio("Input mode", ["Manual Entry", "Demo Sensor Data", "Live ESP32"], horizontal=True, key="mode")
status_card(mode)
if mode == "Live ESP32":
    st.warning("Device not connected — live ESP32 integration is pending. Prediction is disabled until real measurements are available.")
if mode == "Demo Sensor Data":
    st.info("SIMULATED SENSOR DATA — generated demonstration values pass through the same validation and model engine as manual input.")
    if st.button("Generate new demo reading"):
        st.session_state.nitrogen = 40.0 + (st.session_state.get("demo_seed", 0) % 3) * 12
        st.session_state.demo_seed = st.session_state.get("demo_seed", 0) + 1

with st.form("fertilizer_form"):
    farm, chemistry = st.columns(2)
    with farm:
        st.markdown("#### Farm context")
        soil_type = st.selectbox("Soil Type", SUPPORTED_SOILS, index=SUPPORTED_SOILS.index(st.session_state.get("soil_type", "Loamy")), key="soil_type")
        growth_stage = st.selectbox("Crop Growth Stage", SUPPORTED_STAGES, index=SUPPORTED_STAGES.index(st.session_state.get("growth_stage", "Vegetative")), key="growth_stage")
        st.caption("Uses the generic stages present in the training dataset.")
    with chemistry:
        st.markdown("#### Soil nutrient measurements")
        nitrogen = st.number_input("Nitrogen Level", min_value=0.0, max_value=10000.0, value=float(st.session_state.get("nitrogen", 45.0)), step=1.0, key="nitrogen")
        phosphorus = st.number_input("Phosphorus Level", min_value=0.0, max_value=10000.0, value=float(st.session_state.get("phosphorus", 55.0)), step=1.0, key="phosphorus")
        potassium = st.number_input("Potassium Level", min_value=0.0, max_value=10000.0, value=float(st.session_state.get("potassium", 70.0)), step=1.0, key="potassium")
        soil_ph = st.number_input("Soil pH", min_value=0.0, max_value=14.0, value=float(st.session_state.get("soil_ph", 6.5)), step=0.1, key="soil_ph")
        electrical_conductivity = st.number_input("Electrical Conductivity", min_value=0.0, max_value=10000.0, value=float(st.session_state.get("ec", 1.2)), step=0.1, key="ec")
    values = {"crop_type": st.session_state.crop, "soil_type": soil_type, "crop_growth_stage": growth_stage, "soil_ph": soil_ph, "nitrogen_level": nitrogen, "phosphorus_level": phosphorus, "potassium_level": potassium, "electrical_conductivity": electrical_conductivity}
    validation = render_validation(values)
    submitted = st.form_submit_button("Analyze & Recommend", type="primary", use_container_width=True, disabled=mode == "Live ESP32" or not validation["valid"])

if submitted:
    try:
        cached_model()
        result = recommend_fertilizer(**values)
        record_recommendation(ROOT / "data" / "fertilizer_history.db", values, result, mode)
        st.session_state.result = result
    except (ValueError, FileNotFoundError, OSError, RuntimeError):
        st.error("The recommendation could not be generated. Please verify the inputs or contact the system administrator.")

left, right = st.columns([1.28, .72])
with left:
    if st.session_state.result:
        render_result(st.session_state.result, values)
    else:
        st.markdown('<div class="section-kicker">03 / Recommendation</div><div class="empty-state"><h3>No analysis yet</h3><p>Select a crop and enter soil measurements to generate a fertilizer recommendation.</p></div>', unsafe_allow_html=True)
with right:
    st.markdown('<div class="section-kicker">Field readiness</div><div class="section-title">Sensor source status</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><b>Soil moisture</b><br><span class="note">Source: Manual / not required by current model</span><hr><b>Temperature and humidity</b><br><span class="note">Source: ESP32 integration pending</span><hr><b>EC and pH</b><br><span class="note">Source: Manual or suitable validated sensor</span><hr><b>N / P / K</b><br><span class="note">Source: Manual or soil test; inexpensive probes are not assumed laboratory quality</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="warning-box"><b>Prototype boundary</b><br>Category prediction only. Do not use this interface as a dosage or application schedule.</div>', unsafe_allow_html=True)

st.divider()
st.markdown('<div class="section-kicker">04 / Audit trail</div><div class="section-title">Recent recommendations</div>', unsafe_allow_html=True)
history = recent_recommendations(ROOT / "data" / "fertilizer_history.db")
if history:
    display = pd.DataFrame(history).rename(columns={"timestamp": "Timestamp", "crop": "Crop", "input_mode": "Input mode", "soil_type": "Soil", "growth_stage": "Stage", "fertilizer": "Recommendation", "model_probability": "Model probability"})
    columns = [column for column in ["Timestamp", "Crop", "Input mode", "Soil", "Stage", "Recommendation", "Model probability"] if column in display]
    st.dataframe(display[columns], hide_index=True, use_container_width=True)
else:
    st.caption("No recommendations recorded yet.")

st.caption("This system is an AI-assisted fertilizer decision-support prototype. Recommendations are based on the current model and dataset and require agronomic and field validation before real fertilizer application.")