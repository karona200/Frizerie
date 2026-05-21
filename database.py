from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator
from config import config


# ── Engine ─────────────────────────────────────────────────────────────────
engine = create_engine(
    config.database_url,
    connect_args={"check_same_thread": False},  # necesar pentru SQLite
    echo=config.debug,                           # logheaza SQL in terminal
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _rec):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")   # citiri concurente cu scrierea
    cur.execute("PRAGMA busy_timeout=10000") # asteapta 10s inainte sa dea eroare
    cur.execute("PRAGMA synchronous=NORMAL") # sigur cu WAL, mai rapid decat FULL
    cur.close()

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
