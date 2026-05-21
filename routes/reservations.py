from datetime import date, datetime
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from templates_env import templates
from services.appointment_service import AppointmentService
from services.slot_service import SlotService
from services.service_service import ServiceService
from repositories.frizer_repository import FrizerRepository
from schemas import AppointmentCreate
from config import config
from i18n import get_t, SUPPORTED

router = APIRouter(tags=["reservations"])


@router.get("/set-lang/{lang}")
def set_language(lang: str, next: str = "/"):
    if lang not in SUPPORTED:
        lang = "ro"
    response = RedirectResponse(url=next, status_code=303)
    response.set_cookie("lang", lang, max_age=365 * 24 * 3600, httponly=False, samesite="lax")
    return response


@router.get("/", response_class=HTMLResponse)
def booking_page(request: Request, selected_date: str = "", frizer_id: int = None, db: Session = Depends(get_db)):
    """Pagina principala cu formularul de rezervare."""
    today = date.today().isoformat()
    t, lang = get_t(request)

    slots = []
    if selected_date:
        try:
            d = date.fromisoformat(selected_date)
            slots = SlotService(db).get_available_slots(d)
        except ValueError:
            pass

    frizers = FrizerRepository(db).get_all()
    services = []
    if frizer_id:
        services = ServiceService(db).get_all_for_frizer(frizer_id)

    from repositories.gallery_repository import GalleryRepository
    gallery_repo    = GalleryRepository(db)
    all_photos      = gallery_repo.get_all()
    bg_photo        = gallery_repo.get_background()
    carousel_photos = [p for p in all_photos if not p.is_background]

    return templates.TemplateResponse("book.html", {
        "request":        request,
        "app_name":       config.app_name,
        "services":       services,
        "today":          today,
        "selected_date":  selected_date,
        "slots":          slots,
        "frizers":        frizers,
        "selected_frizer_id": frizer_id,
        "gallery_photos": carousel_photos,
        "bg_photo":       bg_photo,
        "t":              t,
        "lang":           lang,
        "supported_langs": SUPPORTED,
    })


@router.post("/book", response_class=HTMLResponse)
def create_booking(
    request:      Request,
    client_name:  str  = Form(...),
    client_phone: str  = Form(...),
    service_id:   int  = Form(...),
    date_str:     str  = Form(..., alias="date"),
    time_str:     str  = Form(..., alias="time"),
    frizer_id:    int  = Form(...),
    db:           Session = Depends(get_db),
):
    """Proceseaza formularul de rezervare si salveaza in DB."""
    t, lang = get_t(request)
    try:
        data = AppointmentCreate(
            client_name=client_name,
            client_phone=client_phone,
            service_id=service_id,
            date=date.fromisoformat(date_str),
            start_time=datetime.strptime(time_str, "%H:%M").time(),
            frizer_id=frizer_id,
        )
        appointment = AppointmentService(db).create(data)
    except ValueError as e:
        slots = SlotService(db).get_available_slots(date.fromisoformat(date_str), frizer_id)
        frizers = FrizerRepository(db).get_all()
        services = ServiceService(db).get_all_for_frizer(frizer_id) if frizer_id else []
        return templates.TemplateResponse("book.html", {
            "request":       request,
            "app_name":      config.app_name,
            "services":      services,
            "today":         date.today().isoformat(),
            "selected_date": date_str,
            "slots":         slots,
            "frizers":       frizers,
            "selected_frizer_id": frizer_id,
            "error":         str(e),
            "t":             t,
            "lang":          lang,
            "supported_langs": SUPPORTED,
        }, status_code=400)

    return RedirectResponse(url=f"/confirmation/{appointment.id}", status_code=303)


@router.get("/confirmation/{appointment_id}", response_class=HTMLResponse)
def confirmation_page(appointment_id: int, request: Request, db: Session = Depends(get_db)):
    """Pagina de confirmare dupa o rezervare reusita."""
    from repositories.appointment_repository import AppointmentRepository
    appointment = AppointmentRepository(db).get_by_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Programarea nu a fost gasita.")

    t, lang = get_t(request)
    return templates.TemplateResponse("confirmation.html", {
        "request":     request,
        "app_name":    config.app_name,
        "appointment": appointment,
        "t":           t,
        "lang":        lang,
        "supported_langs": SUPPORTED,
    })
