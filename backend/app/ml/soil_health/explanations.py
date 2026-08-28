"""Value-derived explanations and recommendations."""


def explain(status: str, stressed: list[dict]) -> tuple[str, str, str | None]:
    if not stressed:
        return "All evaluated parameters are within the validated prototype rules.", "Maintain monitoring and confirm conditions with field observations.", None
    names = [item["name"] for item in stressed]
    return ("Detected stress factors: " + ", ".join(names) + ".", "Monitor " + " and ".join(names) + " and validate corrective action with an agronomist.", names[0])
