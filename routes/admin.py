from datetime import date, datetime
from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.appointment_service import AppointmentService
from repositories.frizer_repository import FrizerRepository
from schemas import AppointmentUpdate
from config import config
import os

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


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

    # Get all frizers for selector
    frizer_repo = FrizerRepository(db)
    frizers = frizer_repo.get_all()
    
    # If no frizer selected, pick the first one
    if not frizer_id and frizers:
        frizer_id = frizers[0].id
    
    service = AppointmentService(db)
    appointments = service.get_by_date_and_frizer(target, frizer_id) if frizer_id else []
    
    selected_frizer = frizer_repo.get_by_id(frizer_id) if frizer_id else None

    return templates.TemplateResponse("admin.html", {
        "request":         request,
        "app_name":        config.app_name,
        "appointments":    appointments,
        "selected_date":   target.isoformat(),
        "today":           today,
        "frizers":         frizers,
        "selected_frizer": selected_frizer,
    })


@router.post("/cancel/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    frizer_id: int = Form(None),
    db: Session = Depends(get_db)
):
    """Anuleaza o programare."""
    try:
        AppointmentService(db).cancel(appointment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    redirect_url = "/admin/dashboard"
    if frizer_id:
        redirect_url += f"?frizer_id={frizer_id}"
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
    
    redirect_url = "/admin/dashboard"
    if frizer_id:
        redirect_url += f"?frizer_id={frizer_id}"
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
def delete_frizer(frizer_id: int, db: Session = Depends(get_db)):
    """Sterge un frizer."""
    frizer = FrizerRepository(db).get_by_id(frizer_id)
    if not frizer:
        raise HTTPException(status_code=404, detail="Frizerul nu exista.")
    
    # Sterge imaginea daca exista
    if frizer.image_path and os.path.exists(frizer.image_path[1:]):  # [1:] pentru a elimina /
        os.remove(frizer.image_path[1:])
    
    FrizerRepository(db).delete_frizer()
    return RedirectResponse(url="/admin/frizers", status_code=303)
