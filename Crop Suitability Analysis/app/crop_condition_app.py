# ============================================================
# SMART AGRICULTURE AI
# CROP CONDITION ASSESSMENT PROTOTYPE
# ============================================================

import sys
from pathlib import Path

import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

CURRENT_DIR = Path(__file__).resolve()

PROJECT_ROOT = CURRENT_DIR.parent.parent

sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT OUR CROP CONDITION ENGINE
# ============================================================

from src.crop_condition_engine import assess_crop_condition


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Smart Agriculture AI",
    page_icon="🌱",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("🌱 Smart Agriculture AI")

st.subheader(
    "Crop Condition Assessment Prototype"
)

st.write(
    """
    This prototype allows farmers or users to manually enter
    current field conditions for Rice or Sugarcane.

    The system then analyzes the entered values using our
    Crop Condition Assessment Engine.
    """
)

st.info(
    "Prototype Mode: Manual inputs simulate data that will "
    "later be received automatically from ESP32 IoT sensors."
)


# ============================================================
# CROP SELECTION
# ============================================================

st.header("🌾 Step 1: Select Crop")

crop = st.selectbox(
    "Select the crop currently grown in the field:",
    [
        "Rice",
        "Sugarcane"
    ]
)


# Convert crop name to lowercase
# because our engine expects:
# rice
# sugarcane

crop_name = crop.lower()


# ============================================================
# SENSOR INPUT SECTION
# ============================================================

st.header(
    "📊 Step 2: Enter Current Field Conditions"
)

st.write(
    "Enter the current measurements from the field."
)


# ============================================================
# ROW 1
# ============================================================

col1, col2, col3 = st.columns(3)


with col1:

    soil_moisture = st.number_input(
        "💧 Soil Moisture (%)",
        min_value=0.0,
        max_value=100.0,
        value=70.0,
        step=1.0
    )


with col2:

    temperature = st.number_input(
        "🌡️ Temperature (°C)",
        min_value=-50.0,
        max_value=70.0,
        value=27.0,
        step=0.5
    )


with col3:

    humidity = st.number_input(
        "💨 Humidity (%)",
        min_value=0.0,
        max_value=100.0,
        value=70.0,
        step=1.0
    )


# ============================================================
# ROW 2
# ============================================================

col4, col5, col6 = st.columns(3)


with col4:

    rainfall = st.number_input(
        "🌧️ Rainfall (mm)",
        min_value=0.0,
        max_value=1000.0,
        value=220.0,
        step=1.0
    )


with col5:

    ph = st.number_input(
        "🧪 Soil pH",
        min_value=0.0,
        max_value=14.0,
        value=6.5,
        step=0.1
    )


with col6:

    nitrogen = st.number_input(
        "🌿 Nitrogen (N)",
        min_value=0.0,
        max_value=1000.0,
        value=80.0,
        step=1.0
    )


# ============================================================
# ROW 3
# ============================================================

col7, col8, col9 = st.columns(3)


with col7:

    phosphorus = st.number_input(
        "🌱 Phosphorus (P)",
        min_value=0.0,
        max_value=1000.0,
        value=45.0,
        step=1.0
    )


with col8:

    potassium = st.number_input(
        "🌾 Potassium (K)",
        min_value=0.0,
        max_value=1000.0,
        value=60.0,
        step=1.0
    )


# ============================================================
# CREATE SENSOR DATA
# ============================================================

sensor_data = {

    "soil_moisture": soil_moisture,

    "temperature": temperature,

    "humidity": humidity,

    "rainfall": rainfall,

    "ph": ph,

    "nitrogen": nitrogen,

    "phosphorus": phosphorus,

    "potassium": potassium
}


# ============================================================
# ASSESSMENT BUTTON
# ============================================================

st.divider()

assess_button = st.button(
    "🔍 Assess Crop Condition",
    type="primary",
    use_container_width=True
)


# ============================================================
# RUN CROP CONDITION ENGINE
# ============================================================

if assess_button:

    try:

        # ----------------------------------------------------
        # CALL OUR ENGINE
        # ----------------------------------------------------

        result = assess_crop_condition(
            crop=crop_name,
            sensor_data=sensor_data
        )


        # ----------------------------------------------------
        # GET RESULTS
        # ----------------------------------------------------

        overall_condition = result[
            "overall_condition"
        ]

        summary = result[
            "summary"
        ]

        parameters = result[
            "parameters"
        ]


        # ----------------------------------------------------
        # DISPLAY OVERALL RESULT
        # ----------------------------------------------------

        st.header(
            "📋 Crop Condition Assessment Result"
        )


        st.write(
            f"Selected Crop: **{crop}**"
        )


        if overall_condition == "OPTIMAL":

            st.success(
                "🟢 Overall Crop Condition: OPTIMAL"
            )


        elif overall_condition == "WARNING":

            st.warning(
                "🟡 Overall Crop Condition: WARNING"
            )


        else:

            st.error(
                "🔴 Overall Crop Condition: CRITICAL"
            )


        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        st.subheader(
            "📊 Condition Summary"
        )


        metric1, metric2, metric3 = st.columns(3)


        with metric1:

            st.metric(
                "🟢 Optimal Parameters",
                summary["optimal"]
            )


        with metric2:

            st.metric(
                "🟡 Warning Parameters",
                summary["warning"]
            )


        with metric3:

            st.metric(
                "🔴 Critical Parameters",
                summary["critical"]
            )


        # ----------------------------------------------------
        # PARAMETER ANALYSIS
        # ----------------------------------------------------

        st.subheader(
            "🔬 Parameter-Level Analysis"
        )


        for parameter, details in parameters.items():

            # Read values

            value = details["value"]

            status = details["status"]

            optimal_range = details[
                "optimal_range"
            ]

            acceptable_range = details[
                "acceptable_range"
            ]


            # Make parameter name readable

            parameter_name = parameter.replace(
                "_",
                " "
            ).title()


            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            if status == "OPTIMAL":

                st.success(
                    f"🟢 {parameter_name}: "
                    f"{value} — OPTIMAL"
                )


            elif status == "WARNING":

                st.warning(
                    f"🟡 {parameter_name}: "
                    f"{value} — WARNING"
                )


            else:

                st.error(
                    f"🔴 {parameter_name}: "
                    f"{value} — CRITICAL"
                )


            # ------------------------------------------------
            # RANGE INFORMATION
            # ------------------------------------------------

            st.caption(
                f"Optimal Range: "
                f"{optimal_range[0]} – "
                f"{optimal_range[1]} | "
                f"Acceptable Range: "
                f"{acceptable_range[0]} – "
                f"{acceptable_range[1]}"
            )


        # ----------------------------------------------------
        # SYSTEM INTERPRETATION
        # ----------------------------------------------------

        st.subheader(
            "💡 System Interpretation"
        )


        if overall_condition == "OPTIMAL":

            st.success(
                f"The current field conditions appear "
                f"to be within the defined optimal "
                f"ranges for {crop}."
            )


        elif overall_condition == "WARNING":

            st.warning(
                f"Some parameters for {crop} are "
                f"outside their optimal ranges. "
                f"Monitoring or corrective action "
                f"may be required."
            )


        else:

            st.error(
                f"One or more parameters for {crop} "
                f"are outside the defined acceptable "
                f"ranges. Immediate attention may "
                f"be required."
            )


        # ----------------------------------------------------
        # TECHNICAL DETAILS
        # ----------------------------------------------------

        with st.expander(
            "🔧 View Technical Assessment Data"
        ):

            st.json(result)


    except Exception as e:

        st.error(
            f"An error occurred: {e}"
        )