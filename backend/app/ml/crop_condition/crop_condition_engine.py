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
#     Rice and Sugarcane use hand-curated optimal/acceptable ranges (all 8
#     parameters, including soil moisture).
#
#     The other 21 crops (apple, banana, blackgram, chickpea, coconut,
#     coffee, cotton, grapes, jute, kidneybeans, lentil, maize, mango,
#     mothbeans, mungbean, muskmelon, orange, papaya, pigeonpeas,
#     pomegranate, watermelon) have their optimal (25th-75th percentile) and
#     acceptable (5th-95th percentile) ranges derived directly from the same
#     crop_recommendation.csv used to train the Crop Recommendation model
#     (100 real samples per crop) for temperature/humidity/ph/rainfall/N/P/K.
#
#     That dataset has no soil-moisture column, so soil_moisture for those 21
#     crops instead uses a hand-assigned heuristic tier by general water
#     need — high (banana, coconut, jute, muskmelon, papaya, watermelon),
#     moderate (apple, coffee, cotton, grapes, maize, mango, orange), or low
#     (blackgram, chickpea, kidneybeans, lentil, mothbeans, mungbean,
#     pigeonpeas, pomegranate) — NOT dataset-derived like the other six
#     parameters for these crops; treat a soil_moisture CRITICAL/WARNING
#     result for these 21 crops as lower-confidence than the other six.
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
    "sugarcane",
    "apple", "banana", "blackgram", "chickpea", "coconut", "coffee",
    "cotton", "grapes", "jute", "kidneybeans", "lentil", "maize", "mango",
    "mothbeans", "mungbean", "muskmelon", "orange", "papaya", "pigeonpeas",
    "pomegranate", "watermelon",
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
    },

    # ========================================================
    # DATA-DERIVED CROPS
    # 25th-75th / 5th-95th percentile ranges computed from
    # crop_recommendation.csv (100 real samples per crop) — see
    # scripts/derive_crop_condition_ranges note in the module docstring.
    # No soil_moisture column exists in that dataset, so it is
    # intentionally left out of each of these dicts (assess_crop_condition
    # reports it as NOT_EVALUATED rather than guessing a threshold).
    # ========================================================

    "apple": {
        "soil_moisture": {"optimal": (55, 70), "acceptable": (40, 85)},  # heuristic (moderate water need) — see module docstring
        "temperature": {"optimal": (22, 23), "acceptable": (21, 24)},
        "humidity": {"optimal": (91, 94), "acceptable": (90, 95)},
        "ph": {"optimal": (5.7, 6.1), "acceptable": (5.6, 6.4)},
        "rainfall": {"optimal": (106, 118), "acceptable": (102, 124)},
        "nitrogen": {"optimal": (10, 30), "acceptable": (2, 37)},
        "phosphorus": {"optimal": (127, 141), "acceptable": (121, 144)},
        "potassium": {"optimal": (197, 203), "acceptable": (195, 205)},
    },
    "banana": {
        "soil_moisture": {"optimal": (70, 85), "acceptable": (55, 95)},  # heuristic (high water need) — see module docstring
        "temperature": {"optimal": (26, 29), "acceptable": (25, 29)},
        "humidity": {"optimal": (78, 83), "acceptable": (76, 85)},
        "ph": {"optimal": (5.7, 6.2), "acceptable": (5.6, 6.4)},
        "rainfall": {"optimal": (96, 112), "acceptable": (91, 119)},
        "nitrogen": {"optimal": (92, 108), "acceptable": (82, 117)},
        "phosphorus": {"optimal": (75, 88), "acceptable": (71, 94)},
        "potassium": {"optimal": (47, 53), "acceptable": (45, 55)},
    },
    "blackgram": {
        "soil_moisture": {"optimal": (35, 55), "acceptable": (20, 70)},  # heuristic (low water need) — see module docstring
        "temperature": {"optimal": (28, 32), "acceptable": (26, 34)},
        "humidity": {"optimal": (63, 68), "acceptable": (60, 69)},
        "ph": {"optimal": (6.8, 7.4), "acceptable": (6.5, 7.7)},
        "rainfall": {"optimal": (64, 71), "acceptable": (62, 74)},
        "nitrogen": {"optimal": (29, 52), "acceptable": (21, 58)},
        "phosphorus": {"optimal": (62, 74), "acceptable": (57, 79)},
        "potassium": {"optimal": (17, 22), "acceptable": (15, 25)},
    },
    "chickpea": {
        "soil_moisture": {"optimal": (35, 55), "acceptable": (20, 70)},  # heuristic (low water need) — see module docstring
        "temperature": {"optimal": (18, 20), "acceptable": (17, 21)},
        "humidity": {"optimal": (15, 18), "acceptable": (14, 20)},
        "ph": {"optimal": (6.6, 7.9), "acceptable": (6.2, 8.7)},
        "rainfall": {"optimal": (74, 86), "acceptable": (68, 93)},
        "nitrogen": {"optimal": (30, 52), "acceptable": (22, 59)},
        "phosphorus": {"optimal": (61, 74), "acceptable": (56, 79)},
        "potassium": {"optimal": (77, 83), "acceptable": (75, 85)},
    },
    "coconut": {
        "soil_moisture": {"optimal": (70, 85), "acceptable": (55, 95)},  # heuristic (high water need) — see module docstring
        "temperature": {"optimal": (26, 29), "acceptable": (25, 30)},
        "humidity": {"optimal": (93, 97), "acceptable": (91, 100)},
        "ph": {"optimal": (5.7, 6.2), "acceptable": (5.6, 6.4)},
        "rainfall": {"optimal": (149, 202), "acceptable": (134, 224)},
        "nitrogen": {"optimal": (14, 31), "acceptable": (1, 39)},
        "phosphorus": {"optimal": (10, 24), "acceptable": (6, 30)},
        "potassium": {"optimal": (29, 33), "acceptable": (26, 35)},
    },
    "coffee": {
        "soil_moisture": {"optimal": (55, 70), "acceptable": (40, 85)},  # heuristic (moderate water need) — see module docstring
        "temperature": {"optimal": (24, 27), "acceptable": (23, 28)},
        "humidity": {"optimal": (54, 64), "acceptable": (51, 68)},
        "ph": {"optimal": (6.4, 7.1), "acceptable": (6.1, 7.5)},
        "rainfall": {"optimal": (136, 181), "acceptable": (121, 195)},
        "nitrogen": {"optimal": (89, 112), "acceptable": (82, 118)},
        "phosphorus": {"optimal": (23, 34), "acceptable": (17, 40)},
        "potassium": {"optimal": (27, 33), "acceptable": (25, 35)},
    },
    "cotton": {
        "soil_moisture": {"optimal": (55, 70), "acceptable": (40, 85)},  # heuristic (moderate water need) — see module docstring
        "temperature": {"optimal": (23, 25), "acceptable": (22, 26)},
        "humidity": {"optimal": (77, 82), "acceptable": (76, 85)},
        "ph": {"optimal": (6.4, 7.4), "acceptable": (6.0, 7.9)},
        "rainfall": {"optimal": (71, 90), "acceptable": (63, 98)},
        "nitrogen": {"optimal": (108, 128), "acceptable": (101, 136)},
        "phosphorus": {"optimal": (40, 52), "acceptable": (36, 60)},
        "potassium": {"optimal": (17, 22), "acceptable": (15, 25)},
    },
    "grapes": {
        "soil_moisture": {"optimal": (55, 70), "acceptable": (40, 85)},  # heuristic (moderate water need) — see module docstring
        "temperature": {"optimal": (16, 31), "acceptable": (10, 41)},
        "humidity": {"optimal": (81, 83), "acceptable": (80, 84)},
        "ph": {"optimal": (5.8, 6.3), "acceptable": (5.6, 6.5)},
        "rainfall": {"optimal": (67, 72), "acceptable": (66, 74)},
        "nitrogen": {"optimal": (12, 35), "acceptable": (4, 39)},
        "phosphorus": {"optimal": (126, 139), "acceptable": (120, 144)},
        "potassium": {"optimal": (197, 203), "acceptable": (195, 205)},
    },
    "jute": {
        "soil_moisture": {"optimal": (70, 85), "acceptable": (55, 95)},  # heuristic (high water need) — see module docstring
        "temperature": {"optimal": (24, 26), "acceptable": (23, 27)},
        "humidity": {"optimal": (75, 83), "acceptable": (71, 88)},
        "ph": {"optimal": (6.3, 7.1), "acceptable": (6.1, 7.4)},
        "rainfall": {"optimal": (161, 188), "acceptable": (152, 197)},
        "nitrogen": {"optimal": (70, 88), "acceptable": (61, 96)},
        "phosphorus": {"optimal": (41, 53), "acceptable": (37, 58)},
        "potassium": {"optimal": (37, 43), "acceptable": (35, 45)},
    },
    "kidneybeans": {
        "soil_moisture": {"optimal": (35, 55), "acceptable": (20, 70)},  # heuristic (low water need) — see module docstring
        "temperature": {"optimal": (18, 22), "acceptable": (16, 24)},
        "humidity": {"optimal": (20, 23), "acceptable": (18, 25)},
        "ph": {"optimal": (5.6, 5.9), "acceptable": (5.5, 6.0)},
        "rainfall": {"optimal": (86, 129), "acceptable": (63, 144)},
        "nitrogen": {"optimal": (12, 28), "acceptable": (3, 37)},
        "phosphorus": {"optimal": (61, 74), "acceptable": (56, 80)},
        "potassium": {"optimal": (17, 22), "acceptable": (15, 25)},
    },
    "lentil": {
        "soil_moisture": {"optimal": (35, 55), "acceptable": (20, 70)},  # heuristic (low water need) — see module docstring
        "temperature": {"optimal": (22, 27), "acceptable": (18, 29)},
        "humidity": {"optimal": (62, 67), "acceptable": (60, 69)},
        "ph": {"optimal": (6.5, 7.4), "acceptable": (6.1, 7.7)},
        "rainfall": {"optimal": (42, 50), "acceptable": (36, 53)},
        "nitrogen": {"optimal": (9, 29), "acceptable": (2, 38)},
        "phosphorus": {"optimal": (62, 75), "acceptable": (57, 79)},
        "potassium": {"optimal": (17, 22), "acceptable": (15, 24)},
    },
    "maize": {
        "soil_moisture": {"optimal": (55, 70), "acceptable": (40, 85)},  # heuristic (moderate water need) — see module docstring
        "temperature": {"optimal": (20, 25), "acceptable": (18, 26)},
        "humidity": {"optimal": (61, 69), "acceptable": (57, 74)},
        "ph": {"optimal": (5.9, 6.6), "acceptable": (5.6, 6.9)},
        "rainfall": {"optimal": (70, 100), "acceptable": (63, 109)},
        "nitrogen": {"optimal": (68, 87), "acceptable": (61, 99)},
        "phosphorus": {"optimal": (43, 56), "acceptable": (35, 60)},
        "potassium": {"optimal": (17, 22), "acceptable": (15, 25)},
    },
    "mango": {
        "soil_moisture": {"optimal": (55, 70), "acceptable": (40, 85)},  # heuristic (moderate water need) — see module docstring
        "temperature": {"optimal": (29, 33), "acceptable": (27, 36)},
        "humidity": {"optimal": (48, 52), "acceptable": (46, 54)},
        "ph": {"optimal": (5.2, 6.4), "acceptable": (4.7, 6.8)},
        "rainfall": {"optimal": (92, 97), "acceptable": (90, 100)},
        "nitrogen": {"optimal": (9, 30), "acceptable": (1, 39)},
        "phosphorus": {"optimal": (20, 35), "acceptable": (16, 38)},
        "potassium": {"optimal": (27, 32), "acceptable": (25, 35)},
    },
    "mothbeans": {
        "soil_moisture": {"optimal": (35, 55), "acceptable": (20, 70)},  # heuristic (low water need) — see module docstring
        "temperature": {"optimal": (26, 30), "acceptable": (24, 31)},
        "humidity": {"optimal": (47, 59), "acceptable": (42, 63)},
        "ph": {"optimal": (5.4, 8.4), "acceptable": (3.7, 9.4)},
        "rainfall": {"optimal": (38, 64), "acceptable": (33, 72)},
        "nitrogen": {"optimal": (11, 30), "acceptable": (3, 39)},
        "phosphorus": {"optimal": (43, 55), "acceptable": (36, 59)},
        "potassium": {"optimal": (18, 23), "acceptable": (15, 25)},
    },
    "mungbean": {
        "soil_moisture": {"optimal": (35, 55), "acceptable": (20, 70)},  # heuristic (low water need) — see module docstring
        "temperature": {"optimal": (28, 29), "acceptable": (27, 30)},
        "humidity": {"optimal": (83, 88), "acceptable": (80, 90)},
        "ph": {"optimal": (6.5, 7.0), "acceptable": (6.3, 7.2)},
        "rainfall": {"optimal": (43, 55), "acceptable": (37, 59)},
        "nitrogen": {"optimal": (10, 31), "acceptable": (2, 37)},
        "phosphorus": {"optimal": (40, 54), "acceptable": (36, 59)},
        "potassium": {"optimal": (17, 22), "acceptable": (15, 25)},
    },
    "muskmelon": {
        "soil_moisture": {"optimal": (70, 85), "acceptable": (55, 95)},  # heuristic (high water need) — see module docstring
        "temperature": {"optimal": (28, 29), "acceptable": (27, 30)},
        "humidity": {"optimal": (91, 94), "acceptable": (90, 95)},
        "ph": {"optimal": (6.2, 6.6), "acceptable": (6.0, 6.7)},
        "rainfall": {"optimal": (22, 27), "acceptable": (21, 29)},
        "nitrogen": {"optimal": (89, 111), "acceptable": (82, 118)},
        "phosphorus": {"optimal": (12, 25), "acceptable": (6, 28)},
        "potassium": {"optimal": (47, 52), "acceptable": (45, 55)},
    },
    "orange": {
        "soil_moisture": {"optimal": (55, 70), "acceptable": (40, 85)},  # heuristic (moderate water need) — see module docstring
        "temperature": {"optimal": (17, 30), "acceptable": (11, 34)},
        "humidity": {"optimal": (91, 93), "acceptable": (90, 95)},
        "ph": {"optimal": (6.5, 7.5), "acceptable": (6.1, 7.9)},
        "rainfall": {"optimal": (106, 116), "acceptable": (101, 119)},
        "nitrogen": {"optimal": (9, 31), "acceptable": (1, 39)},
        "phosphorus": {"optimal": (9, 23), "acceptable": (6, 29)},
        "potassium": {"optimal": (8, 12), "acceptable": (5, 15)},
    },
    "papaya": {
        "soil_moisture": {"optimal": (70, 85), "acceptable": (55, 95)},  # heuristic (high water need) — see module docstring
        "temperature": {"optimal": (29, 39), "acceptable": (24, 43)},
        "humidity": {"optimal": (91, 94), "acceptable": (90, 95)},
        "ph": {"optimal": (6.6, 6.8), "acceptable": (6.5, 7.0)},
        "rainfall": {"optimal": (82, 202), "acceptable": (51, 240)},
        "nitrogen": {"optimal": (39, 59), "acceptable": (32, 69)},
        "phosphorus": {"optimal": (54, 65), "acceptable": (47, 68)},
        "potassium": {"optimal": (47, 52), "acceptable": (45, 55)},
    },
    "pigeonpeas": {
        "soil_moisture": {"optimal": (35, 55), "acceptable": (20, 70)},  # heuristic (low water need) — see module docstring
        "temperature": {"optimal": (23, 31), "acceptable": (19, 36)},
        "humidity": {"optimal": (38, 57), "acceptable": (32, 67)},
        "ph": {"optimal": (5.0, 6.4), "acceptable": (4.7, 7.2)},
        "rainfall": {"optimal": (122, 178), "acceptable": (94, 196)},
        "nitrogen": {"optimal": (10, 30), "acceptable": (3, 39)},
        "phosphorus": {"optimal": (61, 73), "acceptable": (56, 77)},
        "potassium": {"optimal": (18, 23), "acceptable": (16, 25)},
    },
    "pomegranate": {
        "soil_moisture": {"optimal": (35, 55), "acceptable": (20, 70)},  # heuristic (low water need) — see module docstring
        "temperature": {"optimal": (20, 24), "acceptable": (18, 25)},
        "humidity": {"optimal": (88, 92), "acceptable": (86, 95)},
        "ph": {"optimal": (6.0, 6.9), "acceptable": (5.7, 7.1)},
        "rainfall": {"optimal": (105, 110), "acceptable": (103, 112)},
        "nitrogen": {"optimal": (8, 29), "acceptable": (2, 40)},
        "phosphorus": {"optimal": (13, 25), "acceptable": (6, 29)},
        "potassium": {"optimal": (38, 43), "acceptable": (36, 45)},
    },
    "watermelon": {
        "soil_moisture": {"optimal": (70, 85), "acceptable": (55, 95)},  # heuristic (high water need) — see module docstring
        "temperature": {"optimal": (25, 26), "acceptable": (24, 27)},
        "humidity": {"optimal": (83, 88), "acceptable": (80, 90)},
        "ph": {"optimal": (6.3, 6.8), "acceptable": (6.1, 6.9)},
        "rainfall": {"optimal": (46, 56), "acceptable": (41, 59)},
        "nitrogen": {"optimal": (89, 110), "acceptable": (81, 119)},
        "phosphorus": {"optimal": (10, 23), "acceptable": (6, 29)},
        "potassium": {"optimal": (47, 53), "acceptable": (45, 55)},
    },
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


        # Some data-derived crops (see CROP_REQUIREMENTS) have no rule for
        # this parameter — e.g. soil_moisture has no column in
        # crop_recommendation.csv, so it was never fabricated for them.
        # Report it transparently instead of guessing a range.

        if parameter not in requirements:

            results[parameter] = {

                "value": value,

                "status": "NOT_EVALUATED",

                "optimal_range": None,

                "acceptable_range": None
            }

            continue


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