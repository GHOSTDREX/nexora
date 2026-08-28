# ============================================================
# SMART AGRICULTURE AI
# CROP CONDITION ASSESSMENT ENGINE
# ============================================================
#
# Purpose:
#     Evaluate the current condition of a selected crop
#     using sensor and soil parameters.
#
# Supported Crops:
#     - Rice
#     - Sugarcane
#
# Input Parameters:
#     - Soil Moisture
#     - Temperature
#     - Humidity
#     - Rainfall
#     - Soil pH
#     - Nitrogen (N)
#     - Phosphorus (P)
#     - Potassium (K)
#
# Output:
#     - Parameter-level condition:
#           OPTIMAL
#           WARNING
#           CRITICAL
#
#     - Overall crop condition:
#           OPTIMAL
#           WARNING
#           CRITICAL
#
# NOTE:
#     This is currently a rule-based expert system.
#     It is NOT a machine learning model.
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import math


# ============================================================
# SUPPORTED CROPS
# ============================================================

SUPPORTED_CROPS = [
    "rice",
    "sugarcane"
]


# ============================================================
# REQUIRED SENSOR FEATURES
# ============================================================

SENSOR_FEATURES = [
    "soil_moisture",
    "temperature",
    "humidity",
    "rainfall",
    "ph",
    "nitrogen",
    "phosphorus",
    "potassium"
]


# ============================================================
# SENSOR VALUE VALIDATION RANGES
# ============================================================
#
# These ranges are basic technical sanity checks.
# They are NOT agronomic optimal ranges.
#
# Example:
#   Soil moisture cannot logically be below 0% or above 100%.
#   pH should be between 0 and 14.
#
# These checks help protect the system from:
#   - Invalid ESP32 readings
#   - Manual input errors
#   - Sensor failures
#   - Data transmission errors
#
# ============================================================

SENSOR_VALIDATION_RANGES = {

    "soil_moisture": (0, 100),

    "temperature": (-50, 70),

    "humidity": (0, 100),

    "rainfall": (0, 1000),

    "ph": (0, 14),

    "nitrogen": (0, 1000),

    "phosphorus": (0, 1000),

    "potassium": (0, 1000)
}


# ============================================================
# CROP REQUIREMENTS
# ============================================================
#
# Each crop has:
#
#     optimal range
#     acceptable range
#
# Classification:
#
#     Inside optimal range
#         -> OPTIMAL
#
#     Outside optimal but inside acceptable range
#         -> WARNING
#
#     Outside acceptable range
#         -> CRITICAL
#
# ============================================================

CROP_REQUIREMENTS = {

    # ========================================================
    # RICE
    # ========================================================

    "rice": {

        "temperature": {
            "optimal": (20, 30),
            "acceptable": (18, 35)
        },

        "humidity": {
            "optimal": (60, 80),
            "acceptable": (50, 90)
        },

        "soil_moisture": {
            "optimal": (60, 80),
            "acceptable": (40, 90)
        },

        "rainfall": {
            "optimal": (150, 300),
            "acceptable": (100, 400)
        },

        "ph": {
            "optimal": (5.5, 7.0),
            "acceptable": (5.0, 7.5)
        },

        "nitrogen": {
            "optimal": (60, 120),
            "acceptable": (40, 140)
        },

        "phosphorus": {
            "optimal": (30, 70),
            "acceptable": (20, 80)
        },

        "potassium": {
            "optimal": (40, 80),
            "acceptable": (30, 100)
        }
    },


    # ========================================================
    # SUGARCANE
    # ========================================================

    "sugarcane": {

        "temperature": {
            "optimal": (20, 35),
            "acceptable": (18, 40)
        },

        "humidity": {
            "optimal": (60, 80),
            "acceptable": (50, 90)
        },

        "soil_moisture": {
            "optimal": (60, 80),
            "acceptable": (40, 90)
        },

        "rainfall": {
            "optimal": (150, 300),
            "acceptable": (100, 400)
        },

        "ph": {
            "optimal": (6.0, 7.5),
            "acceptable": (5.5, 8.0)
        },

        "nitrogen": {
            "optimal": (80, 150),
            "acceptable": (50, 180)
        },

        "phosphorus": {
            "optimal": (30, 70),
            "acceptable": (20, 90)
        },

        "potassium": {
            "optimal": (80, 150),
            "acceptable": (50, 180)
        }
    }
}


# ============================================================
# FUNCTION: VALIDATE SENSOR DATA
# ============================================================

def validate_sensor_data(sensor_data):
    """
    Validate incoming sensor data.

    Checks:
        1. Input must be a dictionary.
        2. All required parameters must be present.
        3. No required parameters should be missing.
        4. Values must be numeric.
        5. Boolean values are rejected.
        6. Values cannot be NaN or infinite.
        7. Values must be within basic physical/technical ranges.

    Parameters
    ----------
    sensor_data : dict
        Dictionary containing sensor and soil values.

    Raises
    ------
    TypeError
        If sensor_data is not a dictionary.

    ValueError
        If required values are missing or invalid.
    """

    # --------------------------------------------------------
    # Check 1: Input must be dictionary
    # --------------------------------------------------------

    if not isinstance(sensor_data, dict):

        raise TypeError(
            "sensor_data must be a dictionary."
        )


    # --------------------------------------------------------
    # Check 2: Check missing features
    # --------------------------------------------------------

    missing_features = [

        feature

        for feature in SENSOR_FEATURES

        if feature not in sensor_data
    ]


    if missing_features:

        raise ValueError(

            "Missing required sensor parameters: "

            f"{missing_features}"
        )


    # --------------------------------------------------------
    # Check 3: Validate each feature
    # --------------------------------------------------------

    for feature in SENSOR_FEATURES:

        value = sensor_data[feature]


        # ----------------------------------------------------
        # Reject boolean values
        # ----------------------------------------------------

        if isinstance(value, bool):

            raise ValueError(

                f"{feature} must be a numeric value, "
                f"not boolean."
            )


        # ----------------------------------------------------
        # Check numeric type
        # ----------------------------------------------------

        if not isinstance(value, (int, float)):

            raise ValueError(

                f"{feature} must be numeric. "

                f"Received: {value}"
            )


        # ----------------------------------------------------
        # Check NaN and Infinity
        # ----------------------------------------------------

        if not math.isfinite(float(value)):

            raise ValueError(

                f"{feature} contains an invalid "
                f"NaN or infinite value."
            )


        # ----------------------------------------------------
        # Check technical validation range
        # ----------------------------------------------------

        minimum, maximum = SENSOR_VALIDATION_RANGES[feature]


        if not minimum <= value <= maximum:

            raise ValueError(

                f"{feature} value {value} is outside "
                f"the valid technical range "
                f"({minimum}, {maximum})."
            )


# ============================================================
# FUNCTION: ASSESS INDIVIDUAL PARAMETER
# ============================================================

def assess_parameter(
    value,
    optimal_range,
    acceptable_range
):
    """
    Classify one crop parameter.

    Classification logic:

        OPTIMAL
            Value is inside optimal range.

        WARNING
            Value is outside optimal range but
            inside acceptable range.

        CRITICAL
            Value is outside acceptable range.

    Parameters
    ----------
    value : float
        Current sensor or soil value.

    optimal_range : tuple
        Minimum and maximum optimal values.

    acceptable_range : tuple
        Minimum and maximum acceptable values.

    Returns
    -------
    str
        OPTIMAL, WARNING, or CRITICAL.
    """

    optimal_min, optimal_max = optimal_range

    acceptable_min, acceptable_max = acceptable_range


    # --------------------------------------------------------
    # OPTIMAL
    # --------------------------------------------------------

    if optimal_min <= value <= optimal_max:

        return "OPTIMAL"


    # --------------------------------------------------------
    # WARNING
    # --------------------------------------------------------

    elif acceptable_min <= value <= acceptable_max:

        return "WARNING"


    # --------------------------------------------------------
    # CRITICAL
    # --------------------------------------------------------

    else:

        return "CRITICAL"


# ============================================================
# FUNCTION: ASSESS CROP CONDITION
# ============================================================

def assess_crop_condition(
    crop,
    sensor_data
):
    """
    Assess the current condition of a selected crop.

    Parameters
    ----------
    crop : str
        Crop selected by the farmer.
        Supported:
            - rice
            - sugarcane

    sensor_data : dict
        Current sensor and soil values.

    Returns
    -------
    dict
        Structured crop condition assessment.

    Example
    -------
    result = assess_crop_condition(
        crop="rice",
        sensor_data={
            "soil_moisture": 70,
            "temperature": 27,
            "humidity": 72,
            "rainfall": 220,
            "ph": 6.5,
            "nitrogen": 80,
            "phosphorus": 45,
            "potassium": 60
        }
    )
    """

    # ========================================================
    # STEP 1: VALIDATE CROP INPUT
    # ========================================================

    if not isinstance(crop, str):

        raise TypeError(
            "crop must be a string."
        )


    # Convert to lowercase and remove spaces

    crop = crop.lower().strip()


    # Check supported crop

    if crop not in SUPPORTED_CROPS:

        raise ValueError(

            f"Unsupported crop: '{crop}'. "

            f"Supported crops are: "
            f"{SUPPORTED_CROPS}"
        )


    # ========================================================
    # STEP 2: VALIDATE SENSOR DATA
    # ========================================================

    validate_sensor_data(sensor_data)


    # ========================================================
    # STEP 3: GET CROP REQUIREMENTS
    # ========================================================

    requirements = CROP_REQUIREMENTS[crop]


    # ========================================================
    # STEP 4: ASSESS EACH PARAMETER
    # ========================================================

    results = {}


    for parameter in SENSOR_FEATURES:

        # Current sensor value

        value = sensor_data[parameter]


        # Crop-specific optimal range

        optimal_range = requirements[
            parameter
        ]["optimal"]


        # Crop-specific acceptable range

        acceptable_range = requirements[
            parameter
        ]["acceptable"]


        # Assess parameter

        status = assess_parameter(

            value=value,

            optimal_range=optimal_range,

            acceptable_range=acceptable_range
        )


        # Store result

        results[parameter] = {

            "value": value,

            "status": status,

            "optimal_range": optimal_range,

            "acceptable_range": acceptable_range
        }


    # ========================================================
    # STEP 5: COUNT PARAMETER STATUSES
    # ========================================================

    optimal_count = sum(

        1

        for result in results.values()

        if result["status"] == "OPTIMAL"
    )


    warning_count = sum(

        1

        for result in results.values()

        if result["status"] == "WARNING"
    )


    critical_count = sum(

        1

        for result in results.values()

        if result["status"] == "CRITICAL"
    )


    # ========================================================
    # STEP 6: DETERMINE OVERALL CROP CONDITION
    # ========================================================
    #
    # Current prototype business logic:
    #
    # Any critical parameter
    #       -> CRITICAL
    #
    # Two or more warning parameters
    #       -> WARNING
    #
    # Otherwise
    #       -> OPTIMAL
    #
    # NOTE:
    # This aggregation logic should be validated
    # with the client/agronomist before production use.
    #
    # ========================================================

    if critical_count > 0:

        overall_condition = "CRITICAL"


    elif warning_count >= 2:

        overall_condition = "WARNING"


    else:

        overall_condition = "OPTIMAL"


    # ========================================================
    # STEP 7: RETURN STRUCTURED RESULT
    # ========================================================

    return {

        "crop": crop,

        "parameters": results,

        "summary": {

            "optimal": optimal_count,

            "warning": warning_count,

            "critical": critical_count
        },

        "overall_condition": overall_condition
    }


# ============================================================
# LOCAL TESTING
# ============================================================
#
# This section runs ONLY when this file is executed directly:
#
#     python src/crop_condition_engine.py
#
# It does NOT execute when the function is imported
# into the Streamlit application.
#
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "SMART AGRICULTURE AI"
    )

    print(
        "Crop Condition Assessment Engine Test"
    )

    print("=" * 60)


    # ========================================================
    # TEST 1: RICE - OPTIMAL
    # ========================================================

    print("\nTEST 1: Rice - Optimal Scenario")


    rice_optimal_data = {

        "soil_moisture": 70,

        "temperature": 27,

        "humidity": 72,

        "rainfall": 220,

        "ph": 6.5,

        "nitrogen": 80,

        "phosphorus": 45,

        "potassium": 60
    }


    rice_result = assess_crop_condition(

        crop="rice",

        sensor_data=rice_optimal_data
    )


    print(
        "Crop:",
        rice_result["crop"]
    )


    print(
        "Overall Condition:",
        rice_result["overall_condition"]
    )


    print(
        "Summary:",
        rice_result["summary"]
    )


    # ========================================================
    # TEST 2: RICE - CRITICAL
    # ========================================================

    print("\nTEST 2: Rice - Critical Scenario")


    rice_critical_data = {

        "soil_moisture": 20,

        "temperature": 38,

        "humidity": 45,

        "rainfall": 50,

        "ph": 8.0,

        "nitrogen": 20,

        "phosphorus": 15,

        "potassium": 20
    }


    rice_critical_result = assess_crop_condition(

        crop="rice",

        sensor_data=rice_critical_data
    )


    print(
        "Crop:",
        rice_critical_result["crop"]
    )


    print(
        "Overall Condition:",
        rice_critical_result["overall_condition"]
    )


    print(
        "Summary:",
        rice_critical_result["summary"]
    )


    # ========================================================
    # TEST 3: SUGARCANE - OPTIMAL
    # ========================================================

    print("\nTEST 3: Sugarcane - Optimal Scenario")


    sugarcane_optimal_data = {

        "soil_moisture": 70,

        "temperature": 29,

        "humidity": 70,

        "rainfall": 220,

        "ph": 6.8,

        "nitrogen": 110,

        "phosphorus": 50,

        "potassium": 110
    }


    sugarcane_result = assess_crop_condition(

        crop="sugarcane",

        sensor_data=sugarcane_optimal_data
    )


    print(
        "Crop:",
        sugarcane_result["crop"]
    )


    print(
        "Overall Condition:",
        sugarcane_result["overall_condition"]
    )


    print(
        "Summary:",
        sugarcane_result["summary"]
    )


    # ========================================================
    # FINAL TEST SUMMARY
    # ========================================================

    print("\n" + "=" * 60)

    print(
        "ALL BASIC ENGINE TESTS COMPLETED"
    )

    print("=" * 60)