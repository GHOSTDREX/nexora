"""Transparent score calculation for evaluated parameters."""


def calculate_score(evaluated: list[dict]) -> int:
    if not evaluated:
        return 0
    stressed = sum(item["status"] == "Moderate Stress" for item in evaluated)
    return round(100 * (len(evaluated) - stressed) / len(evaluated))


def overall_status(evaluated: list[dict]) -> str:
    if not evaluated:
        return "Not evaluated"
    stress_count = sum(item["status"] == "Moderate Stress" for item in evaluated)
    return "Healthy" if stress_count == 0 else "High Stress" if stress_count >= 3 else "Moderate Stress"
