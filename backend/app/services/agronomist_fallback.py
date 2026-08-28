"""
AgriNova — Rule-based AI Assistant fallback.

Used automatically whenever ANTHROPIC_API_KEY is not configured, so the
Farmer Chatbot still works out of the box. Extends the pattern from the
uploaded Irrigation Recommendation prototype's AgronomistAgent (soil
moisture / timing / weather / soil health / "why did the AI predict this")
with two new topics — crop recommendation and today's weather — and answers
in English, Hindi, or Marathi (the three languages this offline mode
supports; the other seven dropdown languages fall back to English here, but
work fully once an API key enables the LLM path).
"""

SUPPORTED = ("en", "hi", "mr")


def _lang(language: str) -> str:
    return language if language in SUPPORTED else "en"


def _topic(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["crop", "recommend", "grow", "plant", "sow", "फसल", "पिक"]):
        return "crop"
    if any(w in q for w in ["rain", "weather", "forecast", "बारिश", "मौसम", "पाऊस", "हवामान"]):
        return "weather"
    if any(w in q for w in ["moisture", "water", "deficit", "liters", "नमी", "पानी", "ओलावा"]):
        return "moisture"
    if any(w in q for w in ["when", "time", "schedule", "morning", "evening", "कब", "समय", "केव्हा"]):
        return "timing"
    if any(w in q for w in ["ph", "ec", "salinity", "soil", "fertilizer", "मिट्टी", "उर्वरक", "माती", "खत"]):
        return "soil"
    if any(w in q for w in ["why", "predict", "confidence", "model", "क्यों", "मॉडल", "का", "मॉडेल"]):
        return "why"
    if any(w in q for w in ["robot", "lid", "harvest", "रोबोट", "ढक्कन"]):
        return "robot"
    return "greeting"


def build_reply(query: str, language: str, context: dict) -> str:
    lang = _lang(language)
    topic = _topic(query)

    sensor = context.get("sensor") or {}
    farm = context.get("farm") or {}
    irrigation = context.get("irrigation") or {}
    crop_rec = context.get("crop_recommendation") or {}
    weather = context.get("weather") or {}
    robot = context.get("robot") or {}

    sm = sensor.get("soil_moisture", 0)
    temp = sensor.get("temperature", 0)
    hum = sensor.get("humidity", 0)
    crop = farm.get("crop_type", "Wheat")
    pred = irrigation.get("prediction", "Medium")
    conf = irrigation.get("confidence", 0)

    if topic == "crop":
        top = crop_rec.get("top_crop", "—")
        top_conf = crop_rec.get("confidence", 0)
        alts = crop_rec.get("alternatives", [])
        alt_str = ", ".join(f"{a['crop']} ({a['confidence']}%)" for a in alts[:3])
        return {
            "en": f"Based on your latest soil (N/P/K, pH {farm.get('soil_ph', 6.5)}) and climate readings, the AI recommends **{top}** with {top_conf}% confidence. Other suitable options: {alt_str or '—'}.",
            "hi": f"आपकी हाल की मिट्टी (N/P/K, pH {farm.get('soil_ph', 6.5)}) और जलवायु रीडिंग के आधार पर, AI **{top}** की सिफ़ारिश करता है ({top_conf}% विश्वास)। अन्य उपयुक्त विकल्प: {alt_str or '—'}।",
            "mr": f"तुमच्या अलीकडील माती (N/P/K, pH {farm.get('soil_ph', 6.5)}) आणि हवामान नोंदींनुसार, AI **{top}** ची शिफारस करते ({top_conf}% विश्वास). इतर योग्य पर्याय: {alt_str or '—'}.",
        }[lang]

    if topic == "weather":
        wtemp = weather.get("temperature_c")
        whum = weather.get("humidity_pct")
        wrain = weather.get("rain_probability_pct")
        return {
            "en": f"Today's weather: {wtemp}°C, {whum}% humidity, {wrain}% chance of rain. " + (
                "Rain is likely, so you may want to hold off on manual irrigation." if (wrain or 0) > 50
                else "Low rain chance — irrigation planning should rely on your soil moisture reading."
            ),
            "hi": f"आज का मौसम: {wtemp}°C, {whum}% नमी, बारिश की {wrain}% संभावना। " + (
                "बारिश की संभावना अधिक है, इसलिए मैन्युअल सिंचाई रोकना बेहतर होगा।" if (wrain or 0) > 50
                else "बारिश की संभावना कम है — सिंचाई का निर्णय मिट्टी की नमी के आधार पर लें।"
            ),
            "mr": f"आजचे हवामान: {wtemp}°C, {whum}% आर्द्रता, पावसाची {wrain}% शक्यता। " + (
                "पावसाची शक्यता जास्त आहे, त्यामुळे मॅन्युअल सिंचाई थांबवणे योग्य ठरेल." if (wrain or 0) > 50
                else "पावसाची शक्यता कमी आहे — सिंचाईचा निर्णय मातीच्या ओलाव्यावर आधारित घ्या."
            ),
        }[lang]

    if topic == "moisture":
        TARGET_MOISTURE = 55.0
        deficit = max(0.0, TARGET_MOISTURE - sm)
        return {
            "en": f"Your current soil moisture is **{sm}%**. The system targets around {TARGET_MOISTURE}% before pausing irrigation. " + (
                f"That's a deficit of about {deficit:.1f}%, so automatic irrigation should kick in soon." if deficit > 0
                else "You're at or above target — no extra watering needed right now."
            ),
            "hi": f"आपकी वर्तमान मिट्टी की नमी **{sm}%** है। सिस्टम सिंचाई रोकने से पहले लगभग {TARGET_MOISTURE}% का लक्ष्य रखता है। " + (
                f"यानी लगभग {deficit:.1f}% की कमी है, इसलिए स्वचालित सिंचाई जल्द शुरू होनी चाहिए।" if deficit > 0
                else "आप लक्ष्य पर या उससे ऊपर हैं — अभी अतिरिक्त पानी की ज़रूरत नहीं है।"
            ),
            "mr": f"तुमची सध्याची मातीतील ओलावा पातळी **{sm}%** आहे. सिंचाई थांबवण्यापूर्वी प्रणाली सुमारे {TARGET_MOISTURE}% लक्ष्य ठेवते. " + (
                f"म्हणजे सुमारे {deficit:.1f}% ची कमतरता आहे, त्यामुळे स्वयंचलित सिंचाई लवकरच सुरू होईल." if deficit > 0
                else "तुम्ही लक्ष्यावर किंवा त्याहून अधिक आहात — सध्या अतिरिक्त पाण्याची गरज नाही."
            ),
        }[lang]

    if topic == "timing":
        hot = temp > 30
        return {
            "en": "With current temperatures at " + f"{temp}°C, " + (
                "irrigate early morning (5–8 AM) or late evening (6–8 PM) to reduce evaporation loss."
                if hot else "morning irrigation (6–9 AM) is ideal."
            ),
            "hi": f"वर्तमान तापमान {temp}°C होने के कारण, " + (
                "वाष्पीकरण कम करने के लिए सुबह जल्दी (5–8 बजे) या शाम को देर से (6–8 बजे) सिंचाई करें।"
                if hot else "सुबह की सिंचाई (6–9 बजे) आदर्श है।"
            ),
            "mr": f"सध्याचे तापमान {temp}°C असल्याने, " + (
                "बाष्पीभवन कमी करण्यासाठी पहाटे लवकर (5–8) किंवा संध्याकाळी उशिरा (6–8) सिंचन करा."
                if hot else "सकाळी सिंचन (6–9) उत्तम आहे."
            ),
        }[lang]

    if topic == "soil":
        ph = farm.get("soil_ph", 6.5)
        return {
            "en": f"Soil type: {farm.get('soil_type', 'Loamy')}, pH {ph}. " + (
                "Slightly acidic — consider agricultural lime." if ph < 5.5
                else "Slightly alkaline — organic compost can help." if ph > 7.8
                else "Your pH is in a healthy range for most crops."
            ),
            "hi": f"मिट्टी का प्रकार: {farm.get('soil_type', 'Loamy')}, pH {ph}। " + (
                "थोड़ी अम्लीय — कृषि चूना डालने पर विचार करें।" if ph < 5.5
                else "थोड़ी क्षारीय — जैविक खाद मदद कर सकती है।" if ph > 7.8
                else "आपका pH अधिकांश फसलों के लिए स्वस्थ सीमा में है।"
            ),
            "mr": f"मातीचा प्रकार: {farm.get('soil_type', 'Loamy')}, pH {ph}. " + (
                "किंचित आम्लयुक्त — शेतीसाठी चुना वापरण्याचा विचार करा." if ph < 5.5
                else "किंचित अल्कधर्मी — सेंद्रिय खत उपयुक्त ठरू शकते." if ph > 7.8
                else "तुमचा pH बहुतेक पिकांसाठी योग्य श्रेणीत आहे."
            ),
        }[lang]

    if topic == "why":
        return {
            "en": f"The irrigation model predicted **{pred}** water requirement with {conf}% confidence, based on soil moisture ({sm}%), temperature ({temp}°C), and your crop's growth stage ({farm.get('crop_growth_stage', 'Vegetative')}).",
            "hi": f"सिंचाई मॉडल ने मिट्टी की नमी ({sm}%), तापमान ({temp}°C), और फसल की वृद्धि अवस्था ({farm.get('crop_growth_stage', 'Vegetative')}) के आधार पर **{pred}** पानी की आवश्यकता का अनुमान {conf}% विश्वास के साथ लगाया।",
            "mr": f"सिंचन मॉडेलने मातीतील ओलावा ({sm}%), तापमान ({temp}°C), आणि पिकाच्या वाढीच्या टप्प्यावर ({farm.get('crop_growth_stage', 'Vegetative')}) आधारित **{pred}** पाण्याची गरज {conf}% विश्वासाने सांगितली.",
        }[lang]

    if topic == "robot":
        connected = robot.get("robot_connected", True)
        return {
            "en": f"Robot status: {'connected and online' if connected else 'currently disconnected'}. Pump is {'ON' if robot.get('pump_on') else 'OFF'}, rainwater lid is {'OPEN' if robot.get('lid_open') else 'CLOSED'}.",
            "hi": f"रोबोट स्थिति: {'जुड़ा हुआ और ऑनलाइन' if connected else 'फिलहाल डिस्कनेक्ट'}। पंप {'चालू' if robot.get('pump_on') else 'बंद'} है, वर्षा जल ढक्कन {'खुला' if robot.get('lid_open') else 'बंद'} है।",
            "mr": f"रोबोट स्थिती: {'जोडलेले आणि ऑनलाइन' if connected else 'सध्या डिस्कनेक्ट'}. पंप {'चालू' if robot.get('pump_on') else 'बंद'} आहे, पर्जन्य जल झाकण {'उघडे' if robot.get('lid_open') else 'बंद'} आहे.",
        }[lang]

    return {
        "en": f"Hi! I'm your AgriNova AI Assistant for your {farm.get('field_area_hectare', 2.5)} hectare {crop} field. Soil moisture is {sm}%, temperature {temp}°C. Ask me about irrigation, crop recommendations, weather, soil health, or the robot's status.",
        "hi": f"नमस्ते! मैं आपके {farm.get('field_area_hectare', 2.5)} हेक्टेयर {crop} खेत के लिए AgriNova AI सहायक हूँ। मिट्टी की नमी {sm}% है, तापमान {temp}°C है। सिंचाई, फसल सिफारिशों, मौसम, मिट्टी के स्वास्थ्य या रोबोट की स्थिति के बारे में पूछें।",
        "mr": f"नमस्कार! मी तुमच्या {farm.get('field_area_hectare', 2.5)} हेक्टर {crop} शेतासाठी AgriNova AI सहाय्यक आहे. मातीतील ओलावा {sm}% आहे, तापमान {temp}°C आहे. सिंचन, पीक शिफारसी, हवामान, मातीचे आरोग्य किंवा रोबोटच्या स्थितीबद्दल विचारा.",
    }[lang]
