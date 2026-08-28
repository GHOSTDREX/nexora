from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Alert, Farm
from app.deps import get_current_farm
from app.schemas.alert import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    limit: int = 50,
    unread_only: bool = False,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    query = db.query(Alert).filter(Alert.farm_id == farm.id)
    if unread_only:
        query = query.filter(Alert.is_read.is_(False))
    rows = query.order_by(desc(Alert.id)).limit(max(1, min(limit, 200))).all()
    return rows


@router.patch("/{alert_id}/read", response_model=AlertOut)
def mark_read(alert_id: int, farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.farm_id == farm.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/read-all")
def mark_all_read(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    db.query(Alert).filter(Alert.farm_id == farm.id, Alert.is_read.is_(False)).update({"is_read": True})
    db.commit()
    return {"status": "ok"}
