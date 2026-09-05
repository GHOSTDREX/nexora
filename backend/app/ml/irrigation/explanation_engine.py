"""
SMART AGRICULTURE AI
Explanation Engine

Provides dual-layer explainability:
1. Model Explanation (Decision Tree Feature Importances)
2. Agricultural Decision Support (Rule-Based Field Indicators)
"""

# Same 3-language scope as app/services/agronomist_fallback.py's offline
# chatbot — the other seven dropdown languages fall back to English here.
_SUPPORTED = ("en", "hi", "mr")

# Crop growth stage values are English enum values (see farm.crop_growth_stage
# in the DB) — mirrors the table in agronomist_fallback.py so the stage name
# interpolated into indicator #6 below matches the reply's own language.
_STAGE_TR = {
    "hi": {"Sowing": "बुवाई", "Vegetative": "वानस्पतिक अवस्था", "Flowering": "फूल आना", "Harvest": "कटाई"},
    "mr": {"Sowing": "पेरणी", "Vegetative": "वाढीचा टप्पा", "Flowering": "फुलोरा", "Harvest": "कापणी"},
}


class ExplanationEngine:
    @staticmethod
    def generate_agricultural_decision_support(mapped_features, prediction, language="en"):
        """
        Generates agricultural decision-support indicators based on real input values.
        Clearly labeled as decision-support indicators rather than absolute ML rules.
        """
        lang = language if language in _SUPPORTED else "en"

        sm = float(mapped_features.get("Soil_Moisture", 30))
        temp = float(mapped_features.get("Temperature_C", 25))
        rf = float(mapped_features.get("Rainfall_mm", 800))
        ws = float(mapped_features.get("Wind_Speed_kmh", 10))
        stage = str(mapped_features.get("Crop_Growth_Stage", "Vegetative"))
        stage_disp = _STAGE_TR.get(lang, {}).get(stage, stage)
        mulch = str(mapped_features.get("Mulching_Used", "No")).strip().capitalize() == "Yes"

        indicators = []

        def add(en, hi, mr):
            indicators.append({"en": en, "hi": hi, "mr": mr}[lang])

        if sm < 20:
            add(
                "Soil moisture is currently low, indicating increased field water deficit.",
                "मिट्टी की नमी फिलहाल कम है, जिससे खेत में पानी की कमी बढ़ रही है।",
                "मातीतील ओलावा सध्या कमी आहे, त्यामुळे शेतातील पाण्याची कमतरता वाढत आहे.",
            )
        elif sm > 50:
            add(
                "Adequate soil moisture retention minimizes immediate water deficit.",
                "पर्याप्त मिट्टी नमी बनाए रखने से तत्काल पानी की कमी कम होती है।",
                "पुरेसा मातीतील ओलावा टिकवल्याने तत्काळ पाण्याची कमतरता कमी होते.",
            )

        if temp > 32:
            add(
                "Temperature is an important decision-support indicator and is currently elevated.",
                "तापमान एक महत्वपूर्ण निर्णय-सहायक संकेतक है और फिलहाल बढ़ा हुआ है।",
                "तापमान हा एक महत्त्वाचा निर्णय-सहाय्यक निर्देशक आहे आणि सध्या तो वाढलेला आहे.",
            )

        if rf < 300:
            add(
                "Recent cumulative rainfall is limited, indicating low natural water supply.",
                "हाल की संचयी वर्षा सीमित है, जो प्राकृतिक जल आपूर्ति कम होने का संकेत है।",
                "अलीकडील एकूण पर्जन्यमान मर्यादित आहे, जे नैसर्गिक पाणीपुरवठा कमी असल्याचे दर्शवते.",
            )
        elif rf > 1500:
            add(
                "Abundant cumulative rainfall reduces additional irrigation necessity.",
                "प्रचुर संचयी वर्षा अतिरिक्त सिंचाई की आवश्यकता को कम करती है।",
                "मुबलक एकूण पर्जन्यमान अतिरिक्त सिंचनाची गरज कमी करते.",
            )

        if ws > 15:
            add(
                "Moderate to high wind speed can increase surface moisture evaporation.",
                "मध्यम से तेज़ हवा की गति सतह की नमी के वाष्पीकरण को बढ़ा सकती है।",
                "मध्यम ते जास्त वाऱ्याचा वेग पृष्ठभागावरील ओलावा बाष्पीभवन वाढवू शकतो.",
            )

        if stage in ["Flowering", "Vegetative"]:
            indicators.append({
                "en": f"The crop is currently in a sensitive growth stage ({stage_disp}).",
                "hi": f"फसल फिलहाल एक संवेदनशील वृद्धि अवस्था ({stage_disp}) में है।",
                "mr": f"पीक सध्या संवेदनशील वाढीच्या टप्प्यात ({stage_disp}) आहे.",
            }[lang])

        if mulch:
            add(
                "Mulching helps conserve soil moisture and reduce surface evaporation.",
                "मल्चिंग मिट्टी की नमी बचाने और सतह के वाष्पीकरण को कम करने में मदद करती है।",
                "आच्छादन (मल्चिंग) मातीतील ओलावा टिकवण्यास आणि पृष्ठभागावरील बाष्पीभवन कमी करण्यास मदत करते.",
            )

        if prediction == "Low" and not indicators:
            add(
                "Current soil and weather conditions indicate relatively lower irrigation demand.",
                "वर्तमान मिट्टी और मौसम की स्थिति अपेक्षाकृत कम सिंचाई मांग दर्शाती है।",
                "सध्याची माती आणि हवामान स्थिती तुलनेने कमी सिंचनाची गरज दर्शवते.",
            )

        return {
            "title": {
                "en": "Agricultural Decision Support Indicators",
                "hi": "कृषि निर्णय-सहायक संकेतक",
                "mr": "कृषी निर्णय-सहाय्यक निर्देशक",
            }[lang],
            "type": {
                "en": "Rule-based agricultural context",
                "hi": "नियम-आधारित कृषि संदर्भ",
                "mr": "नियम-आधारित कृषी संदर्भ",
            }[lang],
            "indicators": indicators
        }

    @staticmethod
    def generate_model_explanation(engine_instance):
        """
        Extracts Decision Tree pipeline feature importances for Model Explainability.
        """
        if hasattr(engine_instance, "feature_importance_df") and not engine_instance.feature_importance_df.empty:
            top_features = engine_instance.feature_importance_df.head(6).to_dict(orient="records")
            return {
                "title": "Model Explanation",
                "type": "Decision Tree Feature Importances (Gini Index)",
                "top_features": top_features
            }
        return {
            "title": "Model Explanation",
            "type": "Decision Tree Pipeline",
            "top_features": []
        }
