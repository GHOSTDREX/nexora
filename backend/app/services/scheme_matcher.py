"""
AgriNova — Government scheme matcher.

Static, hardcoded reference list of major central-government agriculture
schemes with simple eligibility rules (crop type, land size), matched
against the farm's own profile. No ML, no external API — this is
deliberately just a filter over known public scheme criteria, since the
point is surfacing genuinely relevant schemes, not predicting anything.

Eligibility here is intentionally conservative/illustrative — real
eligibility also depends on state-level rules, documentation, and program
capacity, which is why every scheme links to its official page rather than
claiming a guaranteed entitlement (see disclaimer field).
"""

from typing import Any

_SUPPORTED = ("en", "hi", "mr")

# crops=None / max_land_hectare=None means "no restriction on this axis".
SCHEMES: list[dict[str, Any]] = [
    {
        "id": "pm_kisan",
        "name": "PM-KISAN",
        "link": "https://pmkisan.gov.in",
        "crops": None,
        "max_land_hectare": None,
        "desc": {
            "en": "Direct income support of ₹6,000/year for landholding farmer families, paid in three installments.",
            "hi": "भूमिधारक किसान परिवारों के लिए ₹6,000/वर्ष की प्रत्यक्ष आय सहायता, तीन किस्तों में दी जाती है।",
            "mr": "जमीनधारक शेतकरी कुटुंबांसाठी वार्षिक ₹6,000 थेट उत्पन्न सहाय्य, तीन हप्त्यांमध्ये दिले जाते.",
        },
    },
    {
        "id": "pmfby",
        "name": "PMFBY (Pradhan Mantri Fasal Bima Yojana)",
        "link": "https://pmfby.gov.in",
        "crops": None,
        "max_land_hectare": None,
        "desc": {
            "en": "Low-premium crop insurance covering yield loss from natural calamities, pests, and disease.",
            "hi": "प्राकृतिक आपदाओं, कीट और रोग से होने वाले उपज नुकसान को कवर करने वाला कम-प्रीमियम फसल बीमा।",
            "mr": "नैसर्गिक आपत्ती, कीड आणि रोगामुळे होणाऱ्या उत्पादन नुकसानीला संरक्षण देणारा कमी-हप्त्याचा पीक विमा.",
        },
    },
    {
        "id": "soil_health_card",
        "name": "Soil Health Card Scheme",
        "link": "https://soilhealth.dac.gov.in",
        "crops": None,
        "max_land_hectare": None,
        "desc": {
            "en": "Free periodic soil testing with crop-wise nutrient and fertilizer-dosage recommendations.",
            "hi": "निःशुल्क आवधिक मिट्टी परीक्षण, फसल-वार पोषक तत्व और उर्वरक मात्रा की सिफ़ारिशों के साथ।",
            "mr": "मोफत नियतकालिक माती परीक्षण, पीकनिहाय पोषक व खत मात्रा शिफारसींसह.",
        },
    },
    {
        "id": "kcc",
        "name": "Kisan Credit Card (KCC)",
        "link": "https://www.myscheme.gov.in/schemes/kcc",
        "crops": None,
        "max_land_hectare": None,
        "desc": {
            "en": "Short-term, low-interest credit for crop inputs, working capital, and allied farm activities.",
            "hi": "फसल इनपुट, कार्यशील पूंजी और संबद्ध कृषि गतिविधियों के लिए अल्पकालिक, कम ब्याज वाला ऋण।",
            "mr": "पीक निविष्ठा, खेळते भांडवल आणि संलग्न कृषी कामांसाठी अल्पमुदतीचे, कमी व्याजाचे कर्ज.",
        },
    },
    {
        "id": "pmksy",
        "name": "PM Krishi Sinchayee Yojana (PMKSY)",
        "link": "https://pmksy.gov.in",
        "crops": None,
        "max_land_hectare": None,
        "desc": {
            "en": "Irrigation expansion and water-use-efficiency support, including micro-irrigation subsidy.",
            "hi": "सिंचाई विस्तार और जल-उपयोग-दक्षता सहायता, जिसमें सूक्ष्म सिंचाई सब्सिडी शामिल है।",
            "mr": "सिंचन विस्तार व पाणी-वापर-कार्यक्षमता सहाय्य, ज्यात सूक्ष्म सिंचन अनुदानाचा समावेश आहे.",
        },
    },
    {
        "id": "pdmc",
        "name": "Per Drop More Crop (Micro-Irrigation)",
        "link": "https://pmksy.gov.in/microirrigation/",
        "crops": None,
        "max_land_hectare": 4.0,
        "desc": {
            "en": "Subsidy for drip/sprinkler irrigation systems — most relevant for small and medium landholdings.",
            "hi": "ड्रिप/स्प्रिंकलर सिंचाई प्रणालियों के लिए सब्सिडी — छोटी और मध्यम भूमि जोत के लिए सर्वाधिक प्रासंगिक।",
            "mr": "ठिबक/तुषार सिंचन प्रणालींसाठी अनुदान — लहान व मध्यम शेतजमिनीसाठी सर्वाधिक उपयुक्त.",
        },
    },
    {
        "id": "pkvy",
        "name": "Paramparagat Krishi Vikas Yojana (Organic Farming)",
        "link": "https://pgsindia-ncof.gov.in",
        "crops": None,
        "max_land_hectare": None,
        "desc": {
            "en": "Cluster-based support for converting to certified organic farming practices.",
            "hi": "प्रमाणित जैविक खेती पद्धतियों में बदलाव के लिए क्लस्टर-आधारित सहायता।",
            "mr": "प्रमाणित सेंद्रिय शेती पद्धतीकडे वळण्यासाठी क्लस्टर-आधारित सहाय्य.",
        },
    },
    {
        "id": "nfsm",
        "name": "National Food Security Mission (NFSM)",
        "link": "https://nfsm.gov.in",
        "crops": ["Wheat", "Rice", "Maize", "Cotton"],
        "max_land_hectare": None,
        "desc": {
            "en": "Support for improved seeds, inputs, and practices to raise yield of staple/commercial food crops.",
            "hi": "मुख्य/वाणिज्यिक खाद्य फसलों की उपज बढ़ाने के लिए बेहतर बीज, इनपुट और तरीकों में सहायता।",
            "mr": "मुख्य/व्यावसायिक अन्न पिकांचे उत्पादन वाढवण्यासाठी सुधारित बियाणे, निविष्ठा व पद्धतींसाठी सहाय्य.",
        },
    },
    {
        "id": "smam",
        "name": "Sub-Mission on Agricultural Mechanization (SMAM)",
        "link": "https://agrimachinery.nic.in",
        "crops": None,
        "max_land_hectare": None,
        "min_land_hectare": 1.0,
        "desc": {
            "en": "Subsidy on farm machinery purchase and support for custom-hiring centers.",
            "hi": "कृषि मशीनरी खरीद पर सब्सिडी और कस्टम-हायरिंग केंद्रों के लिए सहायता।",
            "mr": "कृषी यंत्रसामग्री खरेदीवर अनुदान आणि कस्टम-भाडे केंद्रांसाठी सहाय्य.",
        },
    },
    {
        "id": "enam",
        "name": "e-NAM (National Agriculture Market)",
        "link": "https://enam.gov.in",
        "crops": None,
        "max_land_hectare": None,
        "desc": {
            "en": "Online trading platform connecting farmers to mandis nationwide for better price discovery.",
            "hi": "बेहतर मूल्य खोज के लिए किसानों को देशभर की मंडियों से जोड़ने वाला ऑनलाइन ट्रेडिंग प्लेटफ़ॉर्म।",
            "mr": "चांगल्या भाव शोधासाठी शेतकऱ्यांना देशभरातील बाजार समित्यांशी जोडणारे ऑनलाइन व्यापार व्यासपीठ.",
        },
    },
    {
        "id": "rkvy",
        "name": "Rashtriya Krishi Vikas Yojana (RKVY)",
        "link": "https://rkvy.nic.in",
        "crops": None,
        "max_land_hectare": None,
        "desc": {
            "en": "State-implemented umbrella scheme funding a wide range of agriculture and allied-sector projects.",
            "hi": "राज्यों द्वारा कार्यान्वित एक व्यापक योजना जो कृषि और संबद्ध क्षेत्र की परियोजनाओं को वित्तपोषित करती है।",
            "mr": "राज्यांद्वारे राबवली जाणारी व्यापक योजना, जी कृषी व संलग्न क्षेत्रातील प्रकल्पांना निधी पुरवते.",
        },
    },
    {
        "id": "sugarcane_dev",
        "name": "Sugarcane Development Programmes",
        "link": "https://dfpd.gov.in",
        "crops": ["Sugarcane"],
        "max_land_hectare": None,
        "desc": {
            "en": "Support for improved sugarcane varieties, seed replacement, and mill-linked productivity programs.",
            "hi": "बेहतर गन्ना किस्मों, बीज प्रतिस्थापन और मिल-संबद्ध उत्पादकता कार्यक्रमों के लिए सहायता।",
            "mr": "सुधारित ऊस जाती, बियाणे बदल आणि साखर कारखाना-संलग्न उत्पादकता कार्यक्रमांसाठी सहाय्य.",
        },
    },
]

DISCLAIMER = {
    "en": "Illustrative match based on crop and land size only — actual eligibility also depends on state rules and documentation. Confirm on the official scheme page.",
    "hi": "यह मिलान केवल फसल और भूमि के आकार पर आधारित है — वास्तविक पात्रता राज्य के नियमों और दस्तावेज़ों पर भी निर्भर करती है। कृपया आधिकारिक योजना पृष्ठ पर पुष्टि करें।",
    "mr": "हे जुळणी फक्त पीक आणि जमिनीच्या आकारावर आधारित आहे — प्रत्यक्ष पात्रता राज्याच्या नियमांवर आणि कागदपत्रांवरही अवलंबून असते. कृपया अधिकृत योजना पानावर खात्री करा.",
}


def match_schemes(crop_type: str, field_area_hectare: float, language: str = "en") -> dict[str, Any]:
    lang = language if language in _SUPPORTED else "en"
    matches = []
    for scheme in SCHEMES:
        crops = scheme["crops"]
        if crops is not None and crop_type not in crops:
            continue
        max_land = scheme.get("max_land_hectare")
        if max_land is not None and field_area_hectare > max_land:
            continue
        min_land = scheme.get("min_land_hectare")
        if min_land is not None and field_area_hectare < min_land:
            continue
        matches.append({
            "id": scheme["id"],
            "name": scheme["name"],
            "link": scheme["link"],
            "description": scheme["desc"][lang],
        })
    return {"schemes": matches, "disclaimer": DISCLAIMER[lang]}
