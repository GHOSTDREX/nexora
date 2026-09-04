"""
AgriNova — SMS/IVR assistant preview (SIH roadmap item).

Not wired to a real telecom carrier (Twilio etc. costs money we don't have
for this build) — this exists to demonstrate that the query-response logic
behind the chat assistant is transport-agnostic: the same rule-based
`build_reply()` that answers the dashboard chat can just as well answer a
plain-text SMS, which matters for farmers without a smartphone or data plan.
Deliberately uses the offline rule-based fallback, not the Claude API, since
that's the whole point of an SMS channel — it must work with zero data.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Farm
from app.deps import get_current_farm
from app.routers.chat import _gather_context
from app.services.agronomist_fallback import build_reply

router = APIRouter(prefix="/api/sms", tags=["sms"])

# A single GSM SMS segment is 160 chars (7-bit) / 70 chars (Unicode, i.e.
# every non-Latin script here) — 160 kept as a simple, consistent cap for
# the preview rather than modeling real per-script segment math.
SMS_CHAR_LIMIT = 160


class SmsPreviewRequest(BaseModel):
    message: str = Field(min_length=1, max_length=300)
    language: str = "en"


class SmsPreviewResponse(BaseModel):
    reply: str
    truncated: bool


@router.post("/preview", response_model=SmsPreviewResponse)
def sms_preview(
    payload: SmsPreviewRequest,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    context = _gather_context(db, farm)
    reply = build_reply(payload.message, payload.language, context)
    plain = " ".join(reply.split())
    truncated = len(plain) > SMS_CHAR_LIMIT
    if truncated:
        plain = plain[:SMS_CHAR_LIMIT - 1].rstrip() + "…"
    return SmsPreviewResponse(reply=plain, truncated=truncated)
