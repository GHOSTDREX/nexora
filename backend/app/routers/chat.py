from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, SUPPORTED_LANGUAGES
from app.db.database import get_db
from app.db.models import (
    Alert,
    ChatMessage,
    CropRecommendation,
    Farm,
    FarmState,
    IrrigationPrediction,
    SensorReading,
)
from app.deps import get_current_farm
from app.routers.weather import get_today_weather
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agronomist_fallback import build_reply

router = APIRouter(prefix="/api/chat", tags=["chat"])

CHAT_HISTORY_LIMIT = 20


def _gather_context(db: Session, farm: Farm) -> dict:
    reading = (
        db.query(SensorReading).filter(SensorReading.farm_id == farm.id)
        .order_by(desc(SensorReading.id)).first()
    )
    irrigation = (
        db.query(IrrigationPrediction).filter(IrrigationPrediction.farm_id == farm.id)
        .order_by(desc(IrrigationPrediction.id)).first()
    )
    crop_rec = (
        db.query(CropRecommendation).filter(CropRecommendation.farm_id == farm.id)
        .order_by(desc(CropRecommendation.id)).first()
    )
    state = db.query(FarmState).filter(FarmState.farm_id == farm.id).first()
    recent_alerts = (
        db.query(Alert).filter(Alert.farm_id == farm.id).order_by(desc(Alert.id)).limit(5).all()
    )

    try:
        weather = get_today_weather(farm)
    except Exception:
        weather = {}

    return {
        "farm": {
            "name": farm.name, "region": farm.region, "crop_type": farm.crop_type,
            "crop_growth_stage": farm.crop_growth_stage, "soil_type": farm.soil_type,
            "soil_ph": farm.soil_ph, "field_area_hectare": farm.field_area_hectare,
            "season": farm.season, "mulching_used": farm.mulching_used,
            "irrigation_mode": farm.irrigation_mode,
        },
        "sensor": {
            "soil_moisture": reading.soil_moisture, "temperature": reading.temperature,
            "humidity": reading.humidity, "rainfall": reading.rainfall,
            "nitrogen": reading.nitrogen, "phosphorus": reading.phosphorus,
            "potassium": reading.potassium, "rain_detected": reading.rain_detected,
        } if reading else {},
        "irrigation": {
            "prediction": irrigation.prediction, "confidence": irrigation.confidence,
        } if irrigation else {},
        "crop_recommendation": {
            "top_crop": crop_rec.top_crop, "confidence": crop_rec.confidence,
            "alternatives": crop_rec.alternatives,
        } if crop_rec else {},
        "robot": {
            "pump_on": state.pump_on, "lid_open": state.lid_open,
            "robot_connected": state.robot_connected,
        } if state else {},
        "weather": weather,
        "recent_alerts": [{"code": a.code, "severity": a.severity} for a in recent_alerts],
    }


def _call_claude(message: str, language: str, context: dict) -> str:
    import anthropic

    lang_name = SUPPORTED_LANGUAGES.get(language, "English")
    system_prompt = (
        "You are the AgriNova AI Farmer Assistant, embedded in a smart-agriculture dashboard. "
        "You answer a farmer's question using ONLY the live farm context provided below plus your "
        "general agronomy knowledge. Be concise, practical, and warm. Use simple language a farmer "
        f"would understand. Respond ONLY in {lang_name} ({language}).\n\n"
        f"Live farm context (JSON): {context}"
    )
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=600,
        system=system_prompt,
        messages=[{"role": "user", "content": message}],
    )
    return "".join(block.text for block in response.content if hasattr(block, "text"))


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    context = _gather_context(db, farm)

    source = "rule_based"
    reply = None
    if ANTHROPIC_API_KEY:
        try:
            reply = _call_claude(payload.message, payload.language, context)
            source = "llm"
        except Exception:
            reply = None

    if reply is None:
        reply = build_reply(payload.message, payload.language, context)

    db.add(ChatMessage(farm_id=farm.id, role="user", content=payload.message, language=payload.language))
    db.add(ChatMessage(farm_id=farm.id, role="assistant", content=reply, language=payload.language))
    db.commit()

    history = (
        db.query(ChatMessage).filter(ChatMessage.farm_id == farm.id)
        .order_by(desc(ChatMessage.id)).limit(CHAT_HISTORY_LIMIT).all()
    )
    history.reverse()

    return ChatResponse(reply=reply, source=source, history=history)


@router.get("/history", response_model=list)
def chat_history(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    rows = (
        db.query(ChatMessage).filter(ChatMessage.farm_id == farm.id)
        .order_by(desc(ChatMessage.id)).limit(CHAT_HISTORY_LIMIT).all()
    )
    rows.reverse()
    return [{"role": r.role, "content": r.content, "created_at": r.created_at} for r in rows]


@router.get("/prompts")
def suggested_prompts(language: str = "en"):
    prompts = {
        "en": [
            "Which crop should I grow?",
            "Why did the irrigation start?",
            "Is my soil healthy?",
            "What is my NPK level?",
            "Is rain expected today?",
        ],
        "hi": [
            "मुझे कौन सी फसल उगानी चाहिए?",
            "सिंचाई क्यों शुरू हुई?",
            "क्या मेरी मिट्टी स्वस्थ है?",
            "मेरा NPK स्तर क्या है?",
            "क्या आज बारिश की उम्मीद है?",
        ],
        "mr": [
            "मी कोणते पीक घ्यावे?",
            "सिंचन का सुरू झाले?",
            "माझी माती निरोगी आहे का?",
            "माझी NPK पातळी काय आहे?",
            "आज पाऊस अपेक्षित आहे का?",
        ],
    }
    return {"prompts": prompts.get(language, prompts["en"])}
