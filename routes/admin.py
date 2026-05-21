from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from templates_env import templates, SITE
from site_config import get_logo_path, set_logo_path, get_site_name, set_site_name
from services.appointment_service import AppointmentService
from repositories.frizer_repository import FrizerRepository
from schemas import AppointmentUpdate
from config import config
import os

router = APIRouter(prefix="/admin", tags=["admin"])


def _check_password(password: str) -> bool:
    return password == config.admin_password


@router.get("/", response_class=HTMLResponse)
def admin_login_page(request: Request):
    """Pagina de login pentru frizer."""
    return templates.TemplateResponse("admin_login.html", {
        "request":  request,
        "app_name": config.app_name,
    })


@router.post("/", response_class=HTMLResponse)
def admin_login(request: Request, password: str = Form(...)):
    """Verifica parola si redirectioneaza catre panou."""
    if not _check_password(password):
        return templates.TemplateResponse("admin_login.html", {
            "request":  request,
            "app_name": config.app_name,
            "error":    "Parola incorecta.",
        }, status_code=401)
    # MVP simplu: parola corecta → acces direct
    # Viitor: sesiuni / JWT
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(
    request:      Request,
    selected_date: str = "",
    frizer_id: int = None,
    db:           Session = Depends(get_db),
):
    """Panoul frizerului cu toate programarile zilei, filtrate per frizer."""
    today = date.today().isoformat()
    target = date.fromisoformat(selected_date) if selected_date else date.today()

    # Compute week range (Monday..Sunday) containing target
    start_of_week = target - timedelta(days=target.weekday())
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    end_of_week = week_dates[-1]

    # Get all frizers for selector
    frizer_repo = FrizerRepository(db)
    frizers = frizer_repo.get_all()
    
    # If no frizer selected, pick the first one
    if not frizer_id and frizers:
        frizer_id = frizers[0].id
    
    service = AppointmentService(db)
    # Get all appointments for the whole week for selected frizer
    appointments = service.get_by_date_range_and_frizer(start_of_week, end_of_week, frizer_id) if frizer_id else []
    
    selected_frizer = frizer_repo.get_by_id(frizer_id) if frizer_id else None

    return templates.TemplateResponse("admin.html", {
        "request":         request,
        "app_name":        config.app_name,
        "appointments":    appointments,
        "selected_date":   target.isoformat(),
        "week_dates":      week_dates,
        "start_of_week":   start_of_week,
        "end_of_week":     end_of_week,
        "today":           today,
        "frizers":         frizers,
        "selected_frizer": selected_frizer,
    })


@router.post("/cancel/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    frizer_id: int = Form(None),
    selected_date: str = Form(None),
    db: Session = Depends(get_db)
):
    """Anuleaza o programare."""
    try:
        AppointmentService(db).cancel(appointment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    redirect_url = "/admin/dashboard"
    params = []
    if frizer_id:
        params.append(f"frizer_id={frizer_id}")
    if selected_date:
        params.append(f"selected_date={selected_date}")
    if params:
        redirect_url += "?" + "&".join(params)
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/update/{appointment_id}")
def update_appointment(
    appointment_id: int,
    date_str:  str = Form(..., alias="date"),
    time_str:  str = Form(..., alias="time"),
    frizer_id: int = Form(None),
    db: Session = Depends(get_db),
):
    """Modifica data si ora unei programari."""
    try:
        data = AppointmentUpdate(
            date=date.fromisoformat(date_str),
            start_time=datetime.strptime(time_str, "%H:%M").time(),
        )
        AppointmentService(db).update(appointment_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # After update, redirect back to dashboard showing the appointment's date
    redirect_url = "/admin/dashboard"
    params = []
    if frizer_id:
        params.append(f"frizer_id={frizer_id}")
    if date_str:
        params.append(f"selected_date={date_str}")
    if params:
        redirect_url += "?" + "&".join(params)
    return RedirectResponse(url=redirect_url, status_code=303)


# ── Frizer Management ───────────────────────────────────────────────────────
@router.get("/frizers", response_class=HTMLResponse)
def frizers_page(request: Request, db: Session = Depends(get_db)):
    """Lista tuturor frizerilor."""
    frizers = FrizerRepository(db).get_all()
    return templates.TemplateResponse("admin_frizers.html", {
        "request":  request,
        "app_name": config.app_name,
        "frizers":  frizers,
    })


@router.get("/frizers/new", response_class=HTMLResponse)
def new_frizer_page(request: Request):
    """Formular pentru adaugare frizer nou."""
    return templates.TemplateResponse("admin_frizer_form.html", {
        "request":  request,
        "app_name": config.app_name,
        "frizer":   None,
        "is_edit":  False,
    })


@router.post("/frizers", response_class=HTMLResponse)
def create_frizer(
    request:      Request,
    name:         str  = Form(...),
    description:  str  = Form(""),
    image:        UploadFile = File(None),
    db:           Session = Depends(get_db),
):
    """Creeaza un frizer nou."""
    from models import Frizer
    
    image_path = None
    if image and image.filename:
        # Salveaza imaginea
        os.makedirs("static/images/frizers", exist_ok=True)
        file_extension = os.path.splitext(image.filename)[1]
        filename = f"frizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
        file_path = f"static/images/frizers/{filename}"
        
        with open(file_path, "wb") as f:
            f.write(image.file.read())
        image_path = f"/{file_path}"

    # Creaza un frizer NOU (nu actualizeaza pe cel existent)
    new_frizer = Frizer(name=name, description=description, image_path=image_path)
    FrizerRepository(db).create(new_frizer)
    
    return RedirectResponse(url="/admin/frizers", status_code=303)


@router.get("/frizers/{frizer_id}/edit", response_class=HTMLResponse)
def edit_frizer_page(frizer_id: int, request: Request, db: Session = Depends(get_db)):
    """Formular pentru editare frizer."""
    frizer = FrizerRepository(db).get_by_id(frizer_id)
    if not frizer:
        raise HTTPException(status_code=404, detail="Frizerul nu exista.")
    
    return templates.TemplateResponse("admin_frizer_form.html", {
        "request":  request,
        "app_name": config.app_name,
        "frizer":   frizer,
        "is_edit":  True,
    })


@router.post("/frizers/{frizer_id}", response_class=HTMLResponse)
def update_frizer(
    frizer_id:    int,
    request:      Request,
    name:         str  = Form(...),
    description:  str  = Form(""),
    image:        UploadFile = File(None),
    db:           Session = Depends(get_db),
):
    """Actualizeaza un frizer existent."""
    frizer = FrizerRepository(db).get_by_id(frizer_id)
    if not frizer:
        raise HTTPException(status_code=404, detail="Frizerul nu exista.")
    
    image_path = frizer.image_path  # pastreaza imaginea existenta
    if image and image.filename:
        # Salveaza noua imagine
        os.makedirs("static/images/frizers", exist_ok=True)
        file_extension = os.path.splitext(image.filename)[1]
        filename = f"frizer_{frizer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
        file_path = f"static/images/frizers/{filename}"
        
        with open(file_path, "wb") as f:
            f.write(image.file.read())
        image_path = f"/{file_path}"

    frizer.name = name
    frizer.description = description
    frizer.image_path = image_path
    db.commit()
    
    return RedirectResponse(url="/admin/frizers", status_code=303)


@router.post("/frizers/{frizer_id}/delete")
def delete_frizer(frizer_id: int, db: Session = Depends(get_db)):  # noqa: F811
    """Sterge un frizer."""
    frizer = FrizerRepository(db).get_by_id(frizer_id)
    if not frizer:
        raise HTTPException(status_code=404, detail="Frizerul nu exista.")
    
    # Sterge imaginea daca exista
    if frizer.image_path and os.path.exists(frizer.image_path[1:]):  # [1:] pentru a elimina /
        os.remove(frizer.image_path[1:])
    
    FrizerRepository(db).delete_frizer()
    return RedirectResponse(url="/admin/frizers", status_code=303)


# ── Gallery ─────────────────────────────────────────────────────────────────
@router.get("/gallery", response_class=HTMLResponse)
def gallery_page(request: Request, db: Session = Depends(get_db)):
    from repositories.gallery_repository import GalleryRepository
    photos = GalleryRepository(db).get_all()
    return templates.TemplateResponse("admin_gallery.html", {
        "request":  request,
        "app_name": config.app_name,
        "photos":   photos,
    })


@router.post("/gallery/upload")
def upload_gallery_photo(
    caption: str       = Form(""),
    image:   UploadFile = File(...),
    db:      Session   = Depends(get_db),
):
    from repositories.gallery_repository import GalleryRepository
    from models import GalleryPhoto
    if not image or not image.filename:
        return RedirectResponse(url="/admin/gallery", status_code=303)

    os.makedirs("static/images/gallery", exist_ok=True)
    ext      = os.path.splitext(image.filename)[1].lower()
    filename = f"gallery_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}{ext}"
    file_path = f"static/images/gallery/{filename}"
    with open(file_path, "wb") as f:
        f.write(image.file.read())

    photo = GalleryPhoto(file_path=f"/{file_path}", caption=caption.strip() or None)
    GalleryRepository(db).create(photo)
    return RedirectResponse(url="/admin/gallery", status_code=303)


@router.post("/gallery/{photo_id}/delete")
def delete_gallery_photo(photo_id: int, db: Session = Depends(get_db)):
    from repositories.gallery_repository import GalleryRepository
    repo  = GalleryRepository(db)
    photo = repo.get_by_id(photo_id)
    if photo:
        if photo.file_path and os.path.exists(photo.file_path.lstrip("/")):
            os.remove(photo.file_path.lstrip("/"))
        repo.delete(photo)
    return RedirectResponse(url="/admin/gallery", status_code=303)


@router.post("/gallery/{photo_id}/move-up")
def move_photo_up(photo_id: int, db: Session = Depends(get_db)):
    from repositories.gallery_repository import GalleryRepository
    photos = list(GalleryRepository(db).get_all())
    idx = next((i for i, p in enumerate(photos) if p.id == photo_id), None)
    if idx is not None and idx > 0:
        photos[idx - 1], photos[idx] = photos[idx], photos[idx - 1]
        for i, p in enumerate(photos):
            p.sort_order = i
        db.commit()
    return RedirectResponse(url="/admin/gallery", status_code=303)


@router.post("/gallery/{photo_id}/move-down")
def move_photo_down(photo_id: int, db: Session = Depends(get_db)):
    from repositories.gallery_repository import GalleryRepository
    photos = list(GalleryRepository(db).get_all())
    idx = next((i for i, p in enumerate(photos) if p.id == photo_id), None)
    if idx is not None and idx < len(photos) - 1:
        photos[idx], photos[idx + 1] = photos[idx + 1], photos[idx]
        for i, p in enumerate(photos):
            p.sort_order = i
        db.commit()
    return RedirectResponse(url="/admin/gallery", status_code=303)


@router.post("/gallery/{photo_id}/edit-caption")
def edit_caption(
    photo_id: int,
    caption:  str     = Form(""),
    db:       Session = Depends(get_db),
):
    from repositories.gallery_repository import GalleryRepository
    photo = GalleryRepository(db).get_by_id(photo_id)
    if photo:
        photo.caption = caption.strip() or None
        db.commit()
    return RedirectResponse(url="/admin/gallery", status_code=303)


@router.post("/gallery/{photo_id}/set-background")
def set_background(photo_id: int, db: Session = Depends(get_db)):
    from repositories.gallery_repository import GalleryRepository
    repo  = GalleryRepository(db)
    photo = repo.get_by_id(photo_id)
    if photo:
        was_bg = photo.is_background
        for p in repo.get_all():
            p.is_background = False
        if not was_bg:
            photo.is_background = True
        db.commit()
    return RedirectResponse(url="/admin/gallery", status_code=303)


# ── Settings (Logo) ──────────────────────────────────────────────────────────
@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    return templates.TemplateResponse("admin_settings.html", {
        "request":   request,
        "app_name":  config.app_name,
        "logo_path": SITE.get("logo_path"),
        "site_name": SITE.get("site_name") or "",
    })


@router.post("/settings/name")
def save_site_name(name: str = Form("")):
    value = name.strip() or None
    set_site_name(value)
    SITE["site_name"] = value
    return RedirectResponse(url="/admin/settings", status_code=303)


@router.post("/settings/logo/upload")
def upload_logo(image: UploadFile = File(...)):
    if not image or not image.filename:
        return RedirectResponse(url="/admin/settings", status_code=303)
    os.makedirs("static/images/logo", exist_ok=True)
    ext       = os.path.splitext(image.filename)[1].lower()
    file_path = f"static/images/logo/logo{ext}"
    with open(file_path, "wb") as f:
        f.write(image.file.read())
    path = f"/{file_path}"
    set_logo_path(path)
    SITE["logo_path"] = path
    return RedirectResponse(url="/admin/settings", status_code=303)


@router.post("/settings/logo/delete")
def delete_logo():
    current = get_logo_path()
    if current and os.path.exists(current.lstrip("/")):
        os.remove(current.lstrip("/"))
    set_logo_path(None)
    SITE["logo_path"] = None
    return RedirectResponse(url="/admin/settings", status_code=303)
