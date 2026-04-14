from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.service_service import ServiceService
from repositories.frizer_repository import FrizerRepository
from schemas import ServiceRead
from config import config

# Admin routes
admin_router = APIRouter(prefix="/admin/services", tags=["services"])
# Public API routes
public_router = APIRouter(prefix="/services", tags=["public-services"])

templates = Jinja2Templates(directory="templates")


@admin_router.get("/", response_class=HTMLResponse)
def services_page(request: Request, frizer_id: int = None, db: Session = Depends(get_db)):
    frizer_repo = FrizerRepository(db)
    frizers = frizer_repo.get_all()
    
    # If no frizer selected, pick the first one
    if not frizer_id and frizers:
        frizer_id = frizers[0].id
    
    service_service = ServiceService(db)
    services = service_service.get_all_for_frizer(frizer_id) if frizer_id else []
    
    selected_frizer = frizer_repo.get_by_id(frizer_id) if frizer_id else None

    return templates.TemplateResponse("admin_services.html", {
        "request":         request,
        "app_name":        config.app_name,
        "services":        services,
        "frizers":         frizers,
        "selected_frizer": selected_frizer,
        "saved":           request.query_params.get("saved", False),
    })


@admin_router.post("/create", response_class=HTMLResponse)
async def create_service_post(
    request: Request,
    frizer_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    price: str = Form(""),
    db: Session = Depends(get_db)
):
    service_service = ServiceService(db)
    
    try:
        price_int = int(price) if price.strip() else None
        service_service.create_service(name, description or None, price_int, frizer_id)
    except ValueError as e:
        # Handle validation errors
        pass
    
    return RedirectResponse(url=f"/admin/services/?frizer_id={frizer_id}&saved=1", status_code=303)


@admin_router.post("/{service_id}/update", response_class=HTMLResponse)
async def update_service_post(
    service_id: int,
    request: Request,
    frizer_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    price: str = Form(""),
    db: Session = Depends(get_db)
):
    service_service = ServiceService(db)
    
    try:
        price_int = int(price) if price.strip() else None
        service_service.update_service(service_id, name, description or None, price_int)
    except ValueError as e:
        # Handle validation errors
        pass
    
    return RedirectResponse(url=f"/admin/services/?frizer_id={frizer_id}&saved=1", status_code=303)


@admin_router.post("/{service_id}/delete", response_class=HTMLResponse)
async def delete_service_post(
    service_id: int,
    frizer_id: int = Form(...),
    db: Session = Depends(get_db)
):
    service_service = ServiceService(db)
    
    try:
        service_service.delete_service(service_id)
    except ValueError as e:
        # Handle validation errors
        pass
    
    return RedirectResponse(url=f"/admin/services/?frizer_id={frizer_id}&saved=1", status_code=303)


# Public API endpoints
@public_router.get("/frizer/{frizer_id}")
def get_services_for_frizer(frizer_id: int, db: Session = Depends(get_db)):
    """Get all services for a specific frizer (public API for booking page)."""
    service_service = ServiceService(db)
    services = service_service.get_all_for_frizer(frizer_id)
    return [ServiceRead.model_validate(service) for service in services]