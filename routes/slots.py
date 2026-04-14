from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from services.slot_service import SlotService

router = APIRouter(prefix="/slots", tags=["slots"])


@router.get("/{target_date}")
def get_available_slots(
    target_date: date,
    frizer_id: int = Query(..., description="ID of the frizer"),
    db: Session = Depends(get_db)
):
    """
    Returneaza orele disponibile pentru o zi si un frizer specific.
    Genereaza automat sloturile daca nu exista.

    GET /slots/2026-04-15?frizer_id=1
    """
    service = SlotService(db)
    slots = service.get_available_slots(target_date, frizer_id)
    return [
        {"id": s.id, "time": s.start_time.strftime("%H:%M")}
        for s in slots
    ]
