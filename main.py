from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import create_tables, SessionLocal
from config import config
from routes import reservations, admin, slots
from routes.schedule import admin_router as schedule_admin_router, public_router as schedule_public_router
from routes.services import admin_router as services_admin_router, public_router as services_public_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=config.app_name,
        version=config.app_version,
        debug=config.debug,
    )

    app.mount("/static", StaticFiles(directory="static"), name="static")

    app.include_router(reservations.router)
    app.include_router(admin.router)
    app.include_router(slots.router)
    app.include_router(schedule_admin_router)
    app.include_router(schedule_public_router)
    app.include_router(services_admin_router)
    app.include_router(services_public_router)

    @app.on_event("startup")
    def on_startup():
        create_tables()

        # Populeaza orarul implicit la prima pornire
        from services.working_hours_service import WorkingHoursService
        db = SessionLocal()
        try:
            WorkingHoursService(db).seed_defaults()
        finally:
            db.close()

        print(f"\n✓ {config.app_name} v{config.app_version} pornit.")
        print("  → http://localhost:8000               (rezervari clienti)")
        print("  → http://localhost:8000/admin         (panou frizer)")
        print("  → http://localhost:8000/admin/schedule (orar de lucru)")
        print("  → http://localhost:8000/docs          (API docs)\n")

    return app


app = create_app()
