from __future__ import annotations
from typing import Generic, TypeVar, Type, Sequence, Optional
from sqlalchemy.orm import Session
from database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Repository generic cu operatiile CRUD de baza.
    Fiecare model isi va extinde propriul repository din aceasta clasa.

    Folosire:
        class AppointmentRepository(BaseRepository[Appointment]):
            model = Appointment
    """

    model: Type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Read ───────────────────────────────────────────────────
    def get_by_id(self, record_id: int) -> Optional[ModelT]:
        return self.db.get(self.model, record_id)

    def get_all(self) -> Sequence[ModelT]:
        return self.db.query(self.model).all()

    # ── Write ──────────────────────────────────────────────────
    def create(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelT) -> ModelT:
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.commit()
