"""Conservative explanations based on model output and dataset patterns.

Ported (originally unchanged) from
`Fertilizer Recommendation/src/fertilizer_explanation_engine.py`; later
extended with the same 3-language (en/hi/mr) scope used elsewhere in the
offline/rule-based text in this app — see agronomist_fallback.py.
"""

_SUPPORTED = ("en", "hi", "mr")

_STATUS_TR = {
    "hi": {"low": "कम", "moderate": "मध्यम", "high": "अधिक",
           "acidic": "अम्लीय", "alkaline": "क्षारीय", "suitable range": "उपयुक्त सीमा"},
    "mr": {"low": "कमी", "moderate": "मध्यम", "high": "जास्त",
           "acidic": "आम्लयुक्त", "alkaline": "अल्कधर्मी", "suitable range": "योग्य श्रेणी"},
}


def _st(status: str, lang: str) -> str:
    return _STATUS_TR.get(lang, {}).get(status.lower(), status.lower())


def explain_recommendation(fertilizer: str, statuses: dict[str, str], soil_ph: float, language: str = "en") -> str:
    lang = language if language in _SUPPORTED else "en"
    n, p, k, ph_status = statuses['nitrogen'], statuses['phosphorus'], statuses['potassium'], statuses['soil_ph']

    reasons = {
        "en": {
            "Urea": f"Nitrogen is {_st(n, 'en')} relative to the dataset-derived prototype bands. This pattern was associated with Urea recommendations in the training data.",
            "DAP": f"Phosphorus is {_st(p, 'en')} relative to the dataset-derived prototype bands. This pattern was associated with DAP recommendations in the training data.",
            "MOP": f"Potassium is {_st(k, 'en')} relative to the dataset-derived prototype bands. This pattern was associated with MOP recommendations in the training data.",
            "Compost": f"The input soil pH is {soil_ph:.2f} ({_st(ph_status, 'en')}); pH patterns were relevant to Compost recommendations in this training dataset.",
            "Zinc Sulphate": f"The input soil pH is {soil_ph:.2f} ({_st(ph_status, 'en')}); higher-pH patterns were associated with Zinc Sulphate in this training dataset.",
            "NPK": "The combined nitrogen, phosphorus, potassium and pH pattern is consistent with NPK recommendations represented in the training dataset.",
            "SSP": "The nutrient combination matches patterns associated with SSP in the training dataset. The SSP class has limited training support, so additional validation is recommended.",
        },
        "hi": {
            "Urea": f"नाइट्रोजन डेटासेट-व्युत्पन्न मानक सीमाओं की तुलना में {_st(n, 'hi')} है। प्रशिक्षण डेटा में यह पैटर्न यूरिया की सिफ़ारिशों से जुड़ा था।",
            "DAP": f"फॉस्फोरस डेटासेट-व्युत्पन्न मानक सीमाओं की तुलना में {_st(p, 'hi')} है। प्रशिक्षण डेटा में यह पैटर्न DAP की सिफ़ारिशों से जुड़ा था।",
            "MOP": f"पोटैशियम डेटासेट-व्युत्पन्न मानक सीमाओं की तुलना में {_st(k, 'hi')} है। प्रशिक्षण डेटा में यह पैटर्न MOP की सिफ़ारिशों से जुड़ा था।",
            "Compost": f"इनपुट मिट्टी का pH {soil_ph:.2f} ({_st(ph_status, 'hi')}) है; इस प्रशिक्षण डेटासेट में pH पैटर्न कंपोस्ट सिफ़ारिशों के लिए प्रासंगिक थे।",
            "Zinc Sulphate": f"इनपुट मिट्टी का pH {soil_ph:.2f} ({_st(ph_status, 'hi')}) है; इस प्रशिक्षण डेटासेट में उच्च-pH पैटर्न ज़िंक सल्फेट से जुड़े थे।",
            "NPK": "संयुक्त नाइट्रोजन, फॉस्फोरस, पोटैशियम और pH पैटर्न प्रशिक्षण डेटासेट में दर्शाई गई NPK सिफ़ारिशों के अनुरूप है।",
            "SSP": "पोषक तत्व संयोजन प्रशिक्षण डेटासेट में SSP से जुड़े पैटर्न से मेल खाता है। SSP वर्ग का प्रशिक्षण समर्थन सीमित है, इसलिए अतिरिक्त सत्यापन की सिफ़ारिश की जाती है।",
        },
        "mr": {
            "Urea": f"नत्र (नायट्रोजन) डेटासेट-व्युत्पन्न मानक श्रेणींच्या तुलनेत {_st(n, 'mr')} आहे. प्रशिक्षण डेटामध्ये हा नमुना युरिया शिफारसींशी संबंधित होता.",
            "DAP": f"स्फुरद (फॉस्फरस) डेटासेट-व्युत्पन्न मानक श्रेणींच्या तुलनेत {_st(p, 'mr')} आहे. प्रशिक्षण डेटामध्ये हा नमुना DAP शिफारसींशी संबंधित होता.",
            "MOP": f"पालाश (पोटॅशियम) डेटासेट-व्युत्पन्न मानक श्रेणींच्या तुलनेत {_st(k, 'mr')} आहे. प्रशिक्षण डेटामध्ये हा नमुना MOP शिफारसींशी संबंधित होता.",
            "Compost": f"इनपुट मातीचा pH {soil_ph:.2f} ({_st(ph_status, 'mr')}) आहे; या प्रशिक्षण डेटासेटमध्ये pH नमुने कंपोस्ट शिफारसींशी संबंधित होते.",
            "Zinc Sulphate": f"इनपुट मातीचा pH {soil_ph:.2f} ({_st(ph_status, 'mr')}) आहे; या प्रशिक्षण डेटासेटमध्ये जास्त-pH नमुने झिंक सल्फेटशी संबंधित होते.",
            "NPK": "एकत्रित नत्र, स्फुरद, पालाश आणि pH नमुना प्रशिक्षण डेटासेटमध्ये दर्शवलेल्या NPK शिफारसींशी सुसंगत आहे.",
            "SSP": "पोषक घटकांचे संयोजन प्रशिक्षण डेटासेटमधील SSP शी संबंधित नमुन्यांशी जुळते. SSP वर्गाला मर्यादित प्रशिक्षण आधार आहे, त्यामुळे अतिरिक्त पडताळणीची शिफारस केली जाते.",
        },
    }
    fallback = {
        "en": "The recommendation is consistent with patterns represented in the training dataset.",
        "hi": "यह सिफ़ारिश प्रशिक्षण डेटासेट में दर्शाए गए पैटर्न के अनुरूप है।",
        "mr": "ही शिफारस प्रशिक्षण डेटासेटमध्ये दर्शवलेल्या नमुन्यांशी सुसंगत आहे.",
    }[lang]
    return reasons[lang].get(fertilizer, fallback)
