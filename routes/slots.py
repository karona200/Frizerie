from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from services.slot_service import SlotService
from services.working_hours_service import WorkingHoursService

router = APIRouter(prefix="/slots", tags=["slots"])


@router.get("/disabled_dates")
def get_disabled_dates(
    frizer_id: int,
    db: Session = Depends(get_db)
):
    """
    Returneaza lista de date (ISO) pentru care exista override de tip zi libera (is_active=False) pentru frizer.
    """
    service = WorkingHoursService(db)
    overrides = service.get_all_overrides(frizer_id)
    disabled = [o.date.isoformat() for o in overrides if not o.is_active]
    return disabled


@router.get("/closed_weekdays")
def get_closed_weekdays(
    frizer_id: int,
    db: Session = Depends(get_db)
):
    """
    Returneaza zilele saptamanii (JS getDay: 0=Duminica..6=Sambata) pe care frizerul nu lucreaza.
    """
    wh_list = WorkingHoursService(db).get_all_for_frizer(frizer_id)
    # Python weekday 0=Luni..6=Duminica → JS getDay: (py+1)%7
    return [(wh.weekday + 1) % 7 for wh in wh_list if not wh.is_active]


@router.get("/admin/{target_date}")
def get_all_slots_for_admin(
    target_date: date,
    frizer_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Returneaza toate sloturile pentru admin (disponibile + ocupate) cu flag available."""
    from repositories.slot_repository import SlotRepository
    SlotService(db).generate_slots_for_date(target_date, frizer_id)
    all_slots = SlotRepository(db).get_by_date_and_frizer(target_date, frizer_id)
    return [
        {
            "time": s.start_time.strftime("%H:%M"),
            "available": s.is_active and not s.is_booked(),
        }
        for s in all_slots
    ]


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
