"""Value-derived explanations and recommendations."""

_SUPPORTED = ("en", "hi", "mr")

_NO_STRESS = {
    "en": ("All evaluated parameters are within the validated prototype rules.",
           "Maintain monitoring and confirm conditions with field observations."),
    "hi": ("सभी मूल्यांकित मापदंड मान्य प्रोटोटाइप नियमों की सीमा में हैं।",
           "निगरानी बनाए रखें और फ़ील्ड अवलोकन से स्थितियों की पुष्टि करें।"),
    "mr": ("सर्व मूल्यांकित घटक वैध प्रोटोटाइप नियमांच्या मर्यादेत आहेत.",
           "देखरेख सुरू ठेवा आणि क्षेत्रीय निरीक्षणाद्वारे परिस्थितीची पडताळणी करा."),
}

_JOIN_WORD = {"en": "and", "hi": "और", "mr": "आणि"}


def explain(status: str, stressed: list[dict], language: str = "en") -> tuple[str, str, str | None]:
    lang = language if language in _SUPPORTED else "en"
    if not stressed:
        explanation, recommendation = _NO_STRESS[lang]
        return explanation, recommendation, None
    names = [item["name"] for item in stressed]
    join_word = _JOIN_WORD[lang]
    explanation = {
        "en": "Detected stress factors: " + ", ".join(names) + ".",
        "hi": "पहचाने गए तनाव कारक: " + ", ".join(names) + "।",
        "mr": "आढळलेले तणावाचे घटक: " + ", ".join(names) + ".",
    }[lang]
    recommendation = {
        "en": "Monitor " + f" {join_word} ".join(names) + " and validate corrective action with an agronomist.",
        "hi": f" {join_word} ".join(names) + " की निगरानी करें और किसी कृषि विशेषज्ञ से सुधारात्मक कार्रवाई की पुष्टि करें।",
        "mr": f" {join_word} ".join(names) + " वर लक्ष ठेवा आणि कृषी तज्ज्ञाकडून सुधारात्मक कृतीची पडताळणी करा.",
    }[lang]
    return explanation, recommendation, names[0]
