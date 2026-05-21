from datetime import date, datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from services.working_hours_service import WorkingHoursService
from repositories.frizer_repository import FrizerRepository
from config import config
from i18n import get_admin_t, ADMIN_SUPPORTED

admin_router = APIRouter(prefix="/admin/schedule", tags=["admin-schedule"])
public_router = APIRouter(prefix="/schedule", tags=["public-schedule"])

from templates_env import templates


def _sched_ctx(request, days, overrides, frizers, selected_frizer, **extra):
    t, lang = get_admin_t(request)
    day_names = {i: t["days"][(i + 1) % 7] for i in range(7)}
    day_abbr  = {i: t.get("days_short", t["days"])[(i + 1) % 7] for i in range(7)}
    ctx = {
        "request":         request,
        "app_name":        config.app_name,
        "days":            days,
        "overrides":       overrides,
        "frizers":         frizers,
        "selected_frizer": selected_frizer,
        "t":               t,
        "lang":            lang,
        "supported_langs": ADMIN_SUPPORTED,
        "day_names":       day_names,
        "day_abbr":        day_abbr,
    }
    ctx.update(extra)
    return ctx


@admin_router.get("/", response_class=HTMLResponse)
def schedule_page(request: Request, frizer_id: int = None, db: Session = Depends(get_db)):
    frizer_repo = FrizerRepository(db)
    frizers     = frizer_repo.get_all()

    if not frizer_id and frizers:
        return RedirectResponse(url=f"/admin/schedule/?frizer_id={frizers[0].id}", status_code=303)

    service   = WorkingHoursService(db)
    days      = service.get_all_for_frizer(frizer_id) if frizer_id else []
    overrides = service.get_all_overrides(frizer_id) if frizer_id else []
    selected_frizer = frizer_repo.get_by_id(frizer_id) if frizer_id else None

    return templates.TemplateResponse("admin_schedule.html",
        _sched_ctx(request, days, overrides, frizers, selected_frizer,
                   saved=request.query_params.get("saved", False)))


@admin_router.post("/update", response_class=HTMLResponse)
async def update_schedule_post(
    request: Request,
    frizer_id: int = Form(...),
    db: Session = Depends(get_db)
):
    form    = await request.form()
    service = WorkingHoursService(db)
    errors  = []

    for weekday in range(7):
        start_str = form.get(f"start_{weekday}", "")
        end_str   = form.get(f"end_{weekday}",   "")
        is_active = f"active_{weekday}" in form

        if not start_str: start_str = "09:00"
        if not end_str:   end_str   = "17:00"

        try:
            start = datetime.strptime(start_str, "%H:%M").time()
            end   = datetime.strptime(end_str,   "%H:%M").time()
            service.update_day(weekday, start, end, is_active, frizer_id)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        frizer_repo = FrizerRepository(db)
        return templates.TemplateResponse("admin_schedule.html",
            _sched_ctx(request,
                       service.get_all_for_frizer(frizer_id),
                       service.get_all_overrides(frizer_id),
                       frizer_repo.get_all(),
                       frizer_repo.get_by_id(frizer_id),
                       errors=errors), status_code=400)

    return RedirectResponse(url=f"/admin/schedule/?frizer_id={frizer_id}&saved=1", status_code=303)


@admin_router.post("/override", response_class=HTMLResponse)
async def override_schedule_post(
    request: Request,
    frizer_id: int = Form(...),
    db: Session = Depends(get_db)
):
    form    = await request.form()
    service = WorkingHoursService(db)
    errors  = []

    date_str   = form.get("override_date", "")
    start_str  = form.get("override_start", "")
    end_str    = form.get("override_end", "")
    is_day_off = "override_active" in form

    if not date_str:
        errors.append("Trebuie selectata o data pentru setarea exceptionala.")

    if not is_day_off:
        if not start_str or not end_str:
            errors.append("Trebuie completate ambele ore de inceput si sfarsit pentru orar special.")
        is_active = True
    else:
        is_active = False
        start_str = "00:00"
        end_str   = "23:59"

    frizer_repo = FrizerRepository(db)

    if errors:
        return templates.TemplateResponse("admin_schedule.html",
            _sched_ctx(request,
                       service.get_all_for_frizer(frizer_id),
                       service.get_all_overrides(frizer_id),
                       frizer_repo.get_all(),
                       frizer_repo.get_by_id(frizer_id),
                       errors=errors), status_code=400)

    try:
        target_date = date.fromisoformat(date_str)
        start = datetime.strptime(start_str, "%H:%M").time()
        end   = datetime.strptime(end_str,   "%H:%M").time()
        service.update_override(target_date, start, end, is_active, frizer_id)
    except ValueError as e:
        errors.append(str(e))
        return templates.TemplateResponse("admin_schedule.html",
            _sched_ctx(request,
                       service.get_all_for_frizer(frizer_id),
                       service.get_all_overrides(frizer_id),
                       frizer_repo.get_all(),
                       frizer_repo.get_by_id(frizer_id),
                       errors=errors), status_code=400)

    return RedirectResponse(url=f"/admin/schedule/?frizer_id={frizer_id}&saved=1", status_code=303)


@admin_router.post("/override/delete", response_class=HTMLResponse)
async def delete_override_post(
    request: Request,
    frizer_id: int = Form(...),
    db: Session = Depends(get_db)
):
    form = await request.form()
    date_str = form.get("date", "")
    if date_str:
        try:
            service = WorkingHoursService(db)
            service.delete_override(date.fromisoformat(date_str), frizer_id)
        except ValueError:
            pass
    return RedirectResponse(url=f"/admin/schedule/?frizer_id={frizer_id}&saved=1", status_code=303)


@public_router.get("/", response_class=HTMLResponse)
def public_schedule_page(request: Request, db: Session = Depends(get_db)):
    frizer_repo = FrizerRepository(db)
    frizers = frizer_repo.get_all()

    frizer_schedules = []
    service = WorkingHoursService(db)

    for frizer in frizers:
        days = service.get_all_for_frizer(frizer.id)
        overrides = service.get_all_overrides(frizer.id)
        frizer_schedules.append({
            "frizer": frizer,
            "days": days,
            "overrides": overrides
        })

    return templates.TemplateResponse("public_schedule.html", {
        "request": request,
        "app_name": config.app_name,
        "frizer_schedules": frizer_schedules,
    })
