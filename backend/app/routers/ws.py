from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jwt import PyJWTError

from app.core.security import decode_access_token
from app.db.database import SessionLocal
from app.db.models import Farm
from app.services.connection_manager import manager

router = APIRouter()


@router.websocket("/ws/farm")
async def farm_updates(websocket: WebSocket, token: str):
    """Live push channel for one farm. The farm is derived from the JWT
    passed as a query param (?token=...) — never trusted from the client
    directly — so a connection can only ever receive its own farm's data."""
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (PyJWTError, KeyError, ValueError):
        await websocket.close(code=4401)
        return

    db = SessionLocal()
    try:
        farm = db.query(Farm).filter(Farm.owner_id == user_id).first()
    finally:
        db.close()

    if farm is None:
        await websocket.close(code=4404)
        return

    await manager.connect(farm.id, websocket)
    try:
        while True:
            # Clients don't need to send anything; keep the socket alive and
            # drain any pings/messages so disconnects are detected promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(farm.id, websocket)
