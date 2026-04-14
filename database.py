from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator
from config import config


# ── Engine ─────────────────────────────────────────────────────────────────
engine = create_engine(
    config.database_url,
    connect_args={"check_same_thread": False},  # necesar pentru SQLite
    echo=config.debug,                           # logheaza SQL in terminal
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Base model ─────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Clasa de baza pentru toate modelele SQLAlchemy."""
    pass


# ── Dependency injection pentru FastAPI ────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Dependency FastAPI — injecteaza o sesiune DB in fiecare request
    si o inchide automat la final.

    Folosire in route:
        def my_route(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Utilitare ──────────────────────────────────────────────────────────────
def create_tables() -> None:
    """Creeaza toate tabelele daca nu exista."""
    import models  # noqa: F401 - necesar ca SQLAlchemy sa vada toate modelele
    Base.metadata.create_all(bind=engine)
