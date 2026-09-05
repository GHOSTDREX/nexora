"""
AgriNova — WhatsApp bot (SIH roadmap item), Meta WhatsApp Cloud API.

Reuses the exact same offline rule-based `build_reply()` the dashboard chat
and SMS preview already use — a farmer's WhatsApp message and a farmer's
in-app chat message get identical logic, just a different transport. This
matters because most target farmers already have WhatsApp open daily, while
a web app is a bigger ask.

Setup required before this is live (cannot be done from code alone):
  1. Create a Meta developer app (developers.facebook.com) with the
     WhatsApp product added — free tier includes a test phone number.
  2. Set WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID / WHATSAPP_VERIFY_TOKEN
     in backend/.env (see .env.example).
  3. Point the app's webhook at https://<your-public-host>/api/whatsapp/webhook
     — Meta must reach this over the public internet, so local dev needs a
     tunnel (e.g. ngrok) since Meta's servers can't hit localhost.
  4. Each farmer sets their WhatsApp number in Settings so inbound messages
     can be matched to their farm's live context.

Until that's done, GET returns "not_configured" and POST silently no-ops
rather than crashing — same graceful-degradation pattern as the Claude API
key and the Agmarknet mandi-price key.
"""

import logging
import re

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import desc

from app.core.config import WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN
from app.db.database import SessionLocal
from app.db.models import ChatMessage, Farm
from app.routers.chat import _gather_context
from app.services.agronomist_fallback import build_reply

logger = logging.getLogger("agrinova.whatsapp")
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

GRAPH_API_URL = "https://graph.facebook.com/v20.0"


def _normalize_phone(raw: str) -> str:
    """Digits only, last 10 kept as the match key — tolerates +91/91/0
    country-code prefixes and any punctuation a user might type."""
    digits = re.sub(r"\D", "", raw or "")
    return digits[-10:] if len(digits) >= 10 else digits


def _find_farm_by_phone(db, phone: str) -> Farm | None:
    key = _normalize_phone(phone)
    if not key:
        return None
    for farm in db.query(Farm).filter(Farm.whatsapp_number != "").all():
        if _normalize_phone(farm.whatsapp_number) == key:
            return farm
    return None


def _send_whatsapp_message(to: str, text: str) -> bool:
    if not (WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID):
        logger.info("WhatsApp not configured — would have sent to %s: %s", to, text)
        return False
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(
                f"{GRAPH_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages",
                headers={"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "text",
                    "text": {"body": text},
                },
            )
            resp.raise_for_status()
        return True
    except httpx.HTTPError:
        logger.exception("Failed to send WhatsApp message to %s", to)
        return False


@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    if not WHATSAPP_VERIFY_TOKEN:
        raise HTTPException(status_code=503, detail="WhatsApp bot not configured — set WHATSAPP_VERIFY_TOKEN.")
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return int(hub_challenge) if hub_challenge.isdigit() else hub_challenge
    raise HTTPException(status_code=403, detail="Verification token mismatch.")


@router.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()

    try:
        value = payload["entry"][0]["changes"][0]["value"]
        messages = value.get("messages")
        if not messages:
            return {"status": "ignored"}  # delivery/read receipts, not a message
        message = messages[0]
        sender = message["from"]
        text = message.get("text", {}).get("body", "")
    except (KeyError, IndexError):
        return {"status": "ignored"}

    if not text.strip():
        return {"status": "ignored"}

    db = SessionLocal()
    try:
        farm = _find_farm_by_phone(db, sender)
        if farm is None:
            _send_whatsapp_message(
                sender,
                "This number isn't linked to an AgriNova farm yet. Add it in the app under "
                "Settings → WhatsApp Number, then message again.",
            )
            return {"status": "unlinked_number"}

        context = _gather_context(db, farm)
        reply = build_reply(text, farm.owner.preferred_language if farm.owner else "en", context)

        db.add(ChatMessage(farm_id=farm.id, role="user", content=text))
        db.add(ChatMessage(farm_id=farm.id, role="assistant", content=reply))
        db.commit()

        sent = _send_whatsapp_message(sender, reply)
        return {"status": "replied" if sent else "reply_not_sent_not_configured"}
    finally:
        db.close()


@router.get("/status")
def whatsapp_status():
    return {"configured": bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_VERIFY_TOKEN)}
