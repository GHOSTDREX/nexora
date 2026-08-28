"""Conservative explanations based on model output and dataset patterns."""


def explain_recommendation(fertilizer: str, statuses: dict[str, str], soil_ph: float) -> str:
    reasons = {
        "Urea": f"Nitrogen is {statuses['nitrogen'].lower()} relative to the dataset-derived prototype bands. This pattern was associated with Urea recommendations in the training data.",
        "DAP": f"Phosphorus is {statuses['phosphorus'].lower()} relative to the dataset-derived prototype bands. This pattern was associated with DAP recommendations in the training data.",
        "MOP": f"Potassium is {statuses['potassium'].lower()} relative to the dataset-derived prototype bands. This pattern was associated with MOP recommendations in the training data.",
        "Compost": f"The input soil pH is {soil_ph:.2f} ({statuses['soil_ph'].lower()}); pH patterns were relevant to Compost recommendations in this training dataset.",
        "Zinc Sulphate": f"The input soil pH is {soil_ph:.2f} ({statuses['soil_ph'].lower()}); higher-pH patterns were associated with Zinc Sulphate in this training dataset.",
        "NPK": "The combined nitrogen, phosphorus, potassium and pH pattern is consistent with NPK recommendations represented in the training dataset.",
        "SSP": "The nutrient combination matches patterns associated with SSP in the training dataset. The SSP class has limited training support, so additional validation is recommended.",
    }
    return reasons.get(fertilizer, "The recommendation is consistent with patterns represented in the training dataset.")