"""
AgriNova — Rule-based AI Assistant fallback.

Used automatically whenever ANTHROPIC_API_KEY is not configured, so the
Farmer Chatbot still works out of the box. Extends the pattern from the
uploaded Irrigation Recommendation prototype's AgronomistAgent with a much
wider set of general-agriculture topics (pests/disease, fertilizer dosage,
weeds, seed & sowing, harvest & storage, organic practices) in addition to
the farm-specific ones (soil, moisture, timing, irrigation, crop
recommendation, weather, robot, model explanation). Answers in English,
Hindi, or Marathi (the three languages this offline mode supports; the
other seven dropdown languages fall back to English here, but work fully
once an API key enables the LLM path, which also isn't capped to these
topics).
"""

SUPPORTED = ("en", "hi", "mr")


def _lang(language: str) -> str:
    return language if language in SUPPORTED else "en"


# Order matters — first matching topic wins. Farm-specific topics that need
# live sensor/farm context are checked before general-knowledge topics so a
# question like "when should I water" still uses the live temperature.
_TOPIC_KEYWORDS = [
    ("farm_summary", ["about my farm", "farm summary", "farm status", "overview",
                       "मेरे खेत", "खेत के बारे", "खेताबद्दल", "शेताबद्दल"]),
    ("weather", ["rain", "weather", "forecast", "बारिश", "मौसम", "पाऊस", "हवामान"]),
    ("irrigation", ["irrigation", "moisture", "water", "deficit", "liters", "pump",
                     "सिंचाई", "सिंचन", "नमी", "पानी", "ओलावा", "पंप"]),
    ("fertilizer", ["fertilizer", "fertiliser", "npk", "urea", "dap", "mop", "nutrient", "nutrients",
                     "उर्वरक", "खाद", "खत"]),
    ("pest_disease", ["pest", "pests", "insect", "insects", "disease", "diseases", "fungus", "fungal",
                       "bug", "bugs", "worm", "worms", "blight", "rot", "yellowing", "spots on leaves",
                       "कीट", "रोग", "बीमारी", "कीड", "रोगराई"]),
    ("weed", ["weed", "weeds", "weeding", "खरपतवार", "तण"]),
    ("seed_sowing", ["seed rate", "seed spacing", "germinate", "germination", "sowing depth",
                      "planting distance", "बीज दर", "बीज अंतराल", "बियाणे"]),
    ("harvest_storage", ["harvest", "storage", "store grain", "post-harvest", "shelf life",
                          "कटाई", "भंडारण", "काढणी", "साठवण"]),
    ("organic", ["organic", "compost", "vermicompost", "natural farming", "जैविक", "सेंद्रिय", "कंपोस्ट"]),
    ("soil", ["ph", "ec", "salinity", "soil", "मिट्टी", "माती"]),
    ("why", ["why", "predict", "confidence", "model", "क्यों", "मॉडल", "मॉडेल"]),
    ("robot", ["robot", "रोबोट"]),
    ("timing", ["when", "time", "schedule", "morning", "evening", "कब", "समय", "केव्हा"]),
    # Kept last and deliberately generic ("crop"/"grow") so more specific
    # topics above (pest/weed/fertilizer/etc, which are also crop-related)
    # get first claim on a query that mentions both.
    ("crop", ["crop", "crops", "recommend", "which crop", "grow", "growing", "sow", "sows", "sowing crop",
              "फसल", "पिक", "पीक"]),
]

_KEYWORD_RE_CACHE: dict[str, "re.Pattern"] = {}


def _keyword_re(kw: str):
    import re
    pattern = _KEYWORD_RE_CACHE.get(kw)
    if pattern is None:
        pattern = re.compile(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", re.UNICODE)
        _KEYWORD_RE_CACHE[kw] = pattern
    return pattern


def _topic(query: str) -> str:
    q = query.lower()
    for topic, keywords in _TOPIC_KEYWORDS:
        if any(_keyword_re(kw).search(q) for kw in keywords):
            return topic
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

    if topic == "farm_summary":
        return {
            "en": f"**{farm.get('name', 'Your farm')}** — {farm.get('field_area_hectare', 2.5)} ha of {crop} in {farm.get('region', 'your region')} ({farm.get('season', 'Rabi')} season, {farm.get('crop_growth_stage', 'Vegetative')} stage). Soil: {farm.get('soil_type', 'Loamy')}, pH {farm.get('soil_ph', 6.5)}. Live readings: {sm}% soil moisture, {temp}°C, {hum}% humidity. Irrigation mode is {farm.get('irrigation_mode', 'Auto')} and the model currently predicts **{pred}** water need ({conf}% confidence).",
            "hi": f"**{farm.get('name', 'आपका खेत')}** — {farm.get('region', 'आपके क्षेत्र')} में {farm.get('field_area_hectare', 2.5)} हेक्टेयर {crop} ({farm.get('season', 'Rabi')} सीज़न, {farm.get('crop_growth_stage', 'Vegetative')} अवस्था)। मिट्टी: {farm.get('soil_type', 'Loamy')}, pH {farm.get('soil_ph', 6.5)}। वर्तमान रीडिंग: {sm}% नमी, {temp}°C, {hum}% आर्द्रता। सिंचाई मोड {farm.get('irrigation_mode', 'Auto')} है और मॉडल फिलहाल **{pred}** पानी की आवश्यकता का अनुमान लगाता है ({conf}% विश्वास)।",
            "mr": f"**{farm.get('name', 'तुमचे शेत')}** — {farm.get('region', 'तुमच्या भागात')} {farm.get('field_area_hectare', 2.5)} हेक्टर {crop} ({farm.get('season', 'Rabi')} हंगाम, {farm.get('crop_growth_stage', 'Vegetative')} टप्पा). माती: {farm.get('soil_type', 'Loamy')}, pH {farm.get('soil_ph', 6.5)}. सध्याची नोंद: {sm}% ओलावा, {temp}°C, {hum}% आर्द्रता. सिंचन मोड {farm.get('irrigation_mode', 'Auto')} आहे आणि मॉडेल सध्या **{pred}** पाण्याची गरज सांगते ({conf}% विश्वास).",
        }[lang]

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

    if topic == "irrigation":
        TARGET_MOISTURE = 55.0
        deficit = max(0.0, TARGET_MOISTURE - sm)
        pump_on = robot.get("pump_on", False)
        return {
            "en": f"Your current soil moisture is **{sm}%** (target ~{TARGET_MOISTURE}%). Pump is currently **{'ON' if pump_on else 'OFF'}**. " + (
                f"That's a deficit of about {deficit:.1f}%, so automatic irrigation should kick in soon if it hasn't already." if deficit > 0
                else "You're at or above target — no extra watering needed right now."
            ),
            "hi": f"आपकी वर्तमान मिट्टी की नमी **{sm}%** है (लक्ष्य ~{TARGET_MOISTURE}%)। पंप फिलहाल **{'चालू' if pump_on else 'बंद'}** है। " + (
                f"यानी लगभग {deficit:.1f}% की कमी है, इसलिए स्वचालित सिंचाई जल्द शुरू होनी चाहिए।" if deficit > 0
                else "आप लक्ष्य पर या उससे ऊपर हैं — अभी अतिरिक्त पानी की ज़रूरत नहीं है।"
            ),
            "mr": f"तुमची सध्याची मातीतील ओलावा पातळी **{sm}%** आहे (लक्ष्य ~{TARGET_MOISTURE}%). पंप सध्या **{'चालू' if pump_on else 'बंद'}** आहे. " + (
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

    if topic == "fertilizer":
        n = sensor.get("nitrogen")
        p = sensor.get("phosphorus")
        k = sensor.get("potassium")
        return {
            "en": f"Your latest NPK reading is N:{n}, P:{p}, K:{k} (kg/ha). General rule of thumb for {crop}: split nitrogen into 2–3 doses (basal + top-dressing at tillering/flowering) rather than one large dose, since N leaches easily; apply full P and K as basal dose at sowing since they're less mobile in soil. If N is below ~40 or K below ~30, a top-up is usually worth it. Always confirm exact dosage with your local Krishi Vigyan Kendra or soil-testing lab — this is general guidance, not a lab-calibrated recommendation.",
            "hi": f"आपकी हालिया NPK रीडिंग N:{n}, P:{p}, K:{k} (kg/ha) है। {crop} के लिए सामान्य नियम: नाइट्रोजन को एक बड़ी खुराक के बजाय 2–3 भागों में दें (बुवाई + कल्ले निकलते/फूल आते समय), क्योंकि N आसानी से बह जाता है; P और K को बुवाई के समय ही पूरी मात्रा में दें क्योंकि वे मिट्टी में कम गतिशील होते हैं। यह सामान्य मार्गदर्शन है — सटीक मात्रा के लिए अपनी नज़दीकी कृषि विज्ञान केंद्र या मिट्टी परीक्षण प्रयोगशाला से पुष्टि करें।",
            "mr": f"तुमची अलीकडील NPK नोंद N:{n}, P:{p}, K:{k} (kg/ha) आहे. {crop} साठी सर्वसाधारण नियम: नत्र (N) एका मोठ्या डोसऐवजी 2–3 वेळा द्या (पेरणी + फुटवे/फुलोरा अवस्थेत), कारण N सहज वाहून जाते; स्फुरद (P) आणि पालाश (K) पेरणीच्या वेळीच पूर्ण द्या कारण ते मातीत कमी हलतात. हे सर्वसाधारण मार्गदर्शन आहे — नेमक्या मात्रेसाठी तुमच्या जवळच्या कृषी विज्ञान केंद्राशी किंवा माती परीक्षण प्रयोगशाळेशी संपर्क साधा.",
        }[lang]

    if topic == "pest_disease":
        return {
            "en": f"For {crop}, keep an eye out for common issues like leaf-eating caterpillars, aphids, and fungal spots (especially in humid weather — your humidity is {hum}% right now). General IPM approach: (1) scout the field weekly, (2) use yellow/blue sticky traps for flying pests, (3) prefer neem-oil or biological controls before chemical pesticides, (4) remove and destroy visibly infected plants/leaves to stop spread, (5) rotate pesticide chemical groups if you do spray, to avoid resistance. For a specific pest/disease diagnosis, a local agriculture extension officer or a photo-based diagnosis app is more reliable than general advice.",
            "hi": f"{crop} में आम समस्याओं पर ध्यान दें जैसे पत्ती खाने वाली इल्लियाँ, एफिड्स, और फफूंद के धब्बे (विशेष रूप से नम मौसम में — अभी आपकी आर्द्रता {hum}% है)। सामान्य IPM तरीका: (1) साप्ताहिक खेत का निरीक्षण करें, (2) उड़ने वाले कीटों के लिए पीले/नीले चिपचिपे जाल का उपयोग करें, (3) रासायनिक कीटनाशकों से पहले नीम तेल या जैविक नियंत्रण अपनाएँ, (4) संक्रमित पौधों/पत्तियों को हटाकर नष्ट करें, (5) छिड़काव करें तो कीटनाशक समूह बदलते रहें ताकि प्रतिरोध न बने। सटीक निदान के लिए स्थानीय कृषि विस्तार अधिकारी से संपर्क करें।",
            "mr": f"{crop} मध्ये सामान्य समस्यांकडे लक्ष द्या जसे की पाने खाणाऱ्या अळ्या, मावा (aphids), आणि बुरशीचे डाग (विशेषतः दमट हवामानात — सध्या आर्द्रता {hum}% आहे). सर्वसाधारण IPM पद्धत: (1) दर आठवड्याला शेताची पाहणी करा, (2) उडणाऱ्या किडींसाठी पिवळे/निळे चिकट सापळे वापरा, (3) रासायनिक कीटकनाशकांआधी निंबोळी तेल किंवा जैविक नियंत्रण वापरा, (4) संक्रमित रोपे/पाने काढून नष्ट करा, (5) फवारणी करत असल्यास कीटकनाशक गट बदलत राहा. नेमक्या निदानासाठी स्थानिक कृषी विस्तार अधिकाऱ्याशी संपर्क साधा.",
        }[lang]

    if topic == "weed":
        return {
            "en": f"For weed control in {crop}: the first 3–6 weeks after sowing are the critical weed-free period — losses are highest if weeds establish then. Options: (1) pre-emergence herbicide right after sowing, (2) one or two hand-weedings/inter-cultivation at 20–25 and 40–45 days, (3) mulching to physically suppress weeds and also conserve soil moisture. Avoid letting weeds seed — that multiplies next season's problem.",
            "hi": f"{crop} में खरपतवार नियंत्रण के लिए: बुवाई के बाद पहले 3–6 सप्ताह सबसे महत्वपूर्ण होते हैं — इस दौरान खरपतवार बढ़ने पर नुकसान सबसे ज़्यादा होता है। विकल्प: (1) बुवाई के तुरंत बाद प्री-इमरजेंस हर्बिसाइड, (2) 20–25 और 40–45 दिन पर एक या दो निराई/गुड़ाई, (3) मल्चिंग से खरपतवार दबाना और नमी भी बचाना। खरपतवार को बीज बनने न दें, वरना अगले सीज़न समस्या बढ़ती है।",
            "mr": f"{crop} मध्ये तण नियंत्रणासाठी: पेरणीनंतरचे पहिले 3–6 आठवडे सर्वात महत्त्वाचे असतात — या काळात तण वाढल्यास नुकसान सर्वाधिक होते. पर्याय: (1) पेरणीनंतर लगेच प्री-इमर्जन्स तणनाशक, (2) 20–25 आणि 40–45 दिवसांनी एक-दोन खुरपणी/कोळपणी, (3) आच्छादन (मल्चिंग) ने तण दाबणे आणि ओलावाही टिकवणे. तणाला बी धरू देऊ नका, नाहीतर पुढील हंगामात समस्या वाढते.",
        }[lang]

    if topic == "seed_sowing":
        return {
            "en": f"For {crop}, always use certified/disease-free seed and treat it with a fungicide or biocontrol agent (like Trichoderma) before sowing to protect against soil-borne disease. Sow at the depth and row spacing recommended for your variety — too deep delays germination, too shallow risks drying out. Check germination rate on a small sample before full sowing if the seed lot is old or was stored in humid conditions.",
            "hi": f"{crop} के लिए हमेशा प्रमाणित/रोगमुक्त बीज का उपयोग करें और मिट्टी जनित रोगों से बचाव के लिए बुवाई से पहले फफूंदनाशक या जैव-नियंत्रक (जैसे ट्राइकोडर्मा) से उपचारित करें। अपनी किस्म के लिए अनुशंसित गहराई और पंक्ति दूरी पर बुवाई करें — ज़्यादा गहरी बुवाई अंकुरण में देरी करती है, बहुत उथली बुवाई सूखने का खतरा बढ़ाती है। यदि बीज पुराना है या नम स्थिति में रखा गया था, तो पूरी बुवाई से पहले एक छोटे नमूने पर अंकुरण दर जांच लें।",
            "mr": f"{crop} साठी नेहमी प्रमाणित/रोगमुक्त बियाणे वापरा आणि मातीजन्य रोगांपासून संरक्षणासाठी पेरणीपूर्वी बुरशीनाशक किंवा जैव-नियंत्रक (उदा. ट्रायकोडर्मा) ने बीजप्रक्रिया करा. तुमच्या जातीसाठी शिफारस केलेल्या खोलीवर आणि ओळींमधील अंतरावर पेरणी करा — जास्त खोल पेरणी उगवण उशिरा करते, खूप उथळ पेरणी वाळण्याचा धोका वाढवते. बियाणे जुने असल्यास किंवा दमट स्थितीत साठवले असल्यास, पूर्ण पेरणीआधी छोट्या नमुन्यावर उगवण दर तपासा.",
        }[lang]

    if topic == "harvest_storage":
        return {
            "en": f"For {crop}, harvest at physiological maturity — too early reduces yield/quality, too late risks shattering/lodging or pest damage in the field. Dry grain to safe moisture (typically 10–12% for cereals) before storage — storing wet grain is the #1 cause of storage losses to mold and insects. Store in clean, dry, well-ventilated containers/bags, and check stored grain periodically for insect activity or heating.",
            "hi": f"{crop} की कटाई शारीरिक परिपक्वता पर करें — बहुत जल्दी करने से उपज/गुणवत्ता घटती है, बहुत देर करने से दाना झड़ने, गिरने या खेत में कीट क्षति का खतरा रहता है। भंडारण से पहले अनाज को सुरक्षित नमी स्तर (अनाज के लिए आमतौर पर 10–12%) तक सुखाएं — गीला अनाज भंडारित करना फफूंद और कीटों से होने वाले नुकसान का सबसे बड़ा कारण है। साफ, सूखे, हवादार बर्तनों/बोरियों में भंडारण करें और समय-समय पर कीट गतिविधि या गर्मी की जांच करें।",
            "mr": f"{crop} ची काढणी शारीरिक परिपक्वतेच्या वेळी करा — खूप लवकर केल्यास उत्पादन/गुणवत्ता कमी होते, खूप उशिरा केल्यास दाणे गळणे, लोळणे किंवा शेतातच किडीचे नुकसान होण्याचा धोका असतो. साठवणीपूर्वी धान्य सुरक्षित ओलाव्यापर्यंत (धान्यासाठी साधारण 10–12%) वाळवा — ओले धान्य साठवणे हे बुरशी आणि किडींमुळे होणाऱ्या नुकसानाचे प्रमुख कारण आहे. स्वच्छ, कोरड्या, हवेशीर भांड्यांत/पोत्यांत साठवा आणि वेळोवेळी कीड किंवा गरमी तपासा.",
        }[lang]

    if topic == "organic":
        return {
            "en": "Organic practices worth adopting even in a conventional system: compost or vermicompost as a base dressing to improve soil structure and microbial life, crop rotation with legumes to fix nitrogen naturally, neem-based biopesticides for common pests, and green manuring between seasons. These improve long-term soil health even if you still use some synthetic inputs — it isn't all-or-nothing.",
            "hi": "पारंपरिक खेती में भी अपनाने लायक जैविक तरीके: मिट्टी की संरचना और सूक्ष्मजीव जीवन सुधारने के लिए कंपोस्ट या वर्मीकंपोस्ट, प्राकृतिक रूप से नाइट्रोजन स्थिर करने के लिए दलहनी फसलों के साथ फसल चक्र, आम कीटों के लिए नीम आधारित जैव-कीटनाशक, और सीज़न के बीच हरी खाद। ये सिंथेटिक इनपुट का उपयोग जारी रखते हुए भी मिट्टी का दीर्घकालिक स्वास्थ्य सुधारते हैं — यह सब-कुछ-या-कुछ-नहीं वाला मामला नहीं है।",
            "mr": "पारंपरिक शेतीतही स्वीकारण्यासारख्या सेंद्रिय पद्धती: मातीची रचना आणि सूक्ष्मजीव जीवन सुधारण्यासाठी कंपोस्ट किंवा गांडूळ खत, नैसर्गिकरित्या नत्र स्थिर करण्यासाठी कडधान्य पिकांसह पीक फेरपालट, सामान्य किडींसाठी निंबोळीवर आधारित जैव-कीटकनाशके, आणि हंगामांदरम्यान हिरवळीचे खत. रासायनिक निविष्ठा वापरत असतानाही या पद्धती मातीचे दीर्घकालीन आरोग्य सुधारतात — हे सर्व-किंवा-काहीच-नाही असे नाही.",
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
            "en": f"Robot status: {'connected and online' if connected else 'currently disconnected'}. Pump is {'ON' if robot.get('pump_on') else 'OFF'}.",
            "hi": f"रोबोट स्थिति: {'जुड़ा हुआ और ऑनलाइन' if connected else 'फिलहाल डिस्कनेक्ट'}। पंप {'चालू' if robot.get('pump_on') else 'बंद'} है।",
            "mr": f"रोबोट स्थिती: {'जोडलेले आणि ऑनलाइन' if connected else 'सध्या डिस्कनेक्ट'}. पंप {'चालू' if robot.get('pump_on') else 'बंद'} आहे.",
        }[lang]

    return {
        "en": f"Hi! I'm your AgriNova AI Assistant for your {farm.get('field_area_hectare', 2.5)} hectare {crop} field. Soil moisture is {sm}%, temperature {temp}°C. Ask me about irrigation, fertilizer dosage, pests & disease, weeds, seeds & sowing, harvest & storage, organic practices, crop recommendations, weather, soil health, or the robot's status.",
        "hi": f"नमस्ते! मैं आपके {farm.get('field_area_hectare', 2.5)} हेक्टेयर {crop} खेत के लिए AgriNova AI सहायक हूँ। मिट्टी की नमी {sm}% है, तापमान {temp}°C है। सिंचाई, उर्वरक मात्रा, कीट व रोग, खरपतवार, बीज व बुवाई, कटाई व भंडारण, जैविक तरीकों, फसल सिफारिशों, मौसम, मिट्टी के स्वास्थ्य या रोबोट की स्थिति के बारे में पूछें।",
        "mr": f"नमस्कार! मी तुमच्या {farm.get('field_area_hectare', 2.5)} हेक्टर {crop} शेतासाठी AgriNova AI सहाय्यक आहे. मातीतील ओलावा {sm}% आहे, तापमान {temp}°C आहे. सिंचन, खताची मात्रा, कीड व रोग, तण, बियाणे व पेरणी, काढणी व साठवण, सेंद्रिय पद्धती, पीक शिफारसी, हवामान, मातीचे आरोग्य किंवा रोबोटच्या स्थितीबद्दल विचारा.",
    }[lang]


if __name__ == "__main__":
    _ctx = {
        "farm": {"name": "Test Farm", "region": "North", "crop_type": "Wheat", "field_area_hectare": 2.5,
                  "soil_type": "Loamy", "soil_ph": 6.5, "season": "Rabi", "crop_growth_stage": "Vegetative",
                  "irrigation_mode": "Auto"},
        "sensor": {"soil_moisture": 40, "temperature": 32, "humidity": 60, "nitrogen": 30, "phosphorus": 20, "potassium": 25},
        "irrigation": {"prediction": "High", "confidence": 92},
        "crop_recommendation": {"top_crop": "rice", "confidence": 87, "alternatives": [{"crop": "maize", "confidence": 60}]},
        "weather": {"temperature_c": 30, "humidity_pct": 55, "rain_probability_pct": 20},
        "robot": {"pump_on": True, "robot_connected": True},
    }
    _queries = [
        "tell me about my farm", "which crop should I grow", "will it rain today",
        "is my soil moisture ok", "when should I irrigate", "how much fertilizer should I use",
        "my plant has pest spots", "how do I control weeds", "what seed rate should I use",
        "when should I harvest", "any organic tips", "what is my soil ph",
        "why did the model predict this", "is the robot connected", "hello",
    ]
    for _q in _queries:
        for _l in ("en", "hi", "mr"):
            _reply = build_reply(_q, _l, _ctx)
            assert isinstance(_reply, str) and _reply, f"empty reply for ({_q!r}, {_l!r})"
    # every topic bucket except the catch-all should be reachable
    _topics_hit = {_topic(q) for q in _queries}
    assert _topics_hit == {t for t, _ in _TOPIC_KEYWORDS} | {"greeting"}, _topics_hit
    print(f"OK — {len(_queries)} queries x 3 languages, {len(_topics_hit)} topics covered")
