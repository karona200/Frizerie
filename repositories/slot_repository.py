from __future__ import annotations
from datetime import date, time
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from models import TimeSlot
from repositories.base import BaseRepository


class SlotRepository(BaseRepository[TimeSlot]):
    """Operatii DB pentru sloturile orare."""

    model = TimeSlot

    def get_by_date(self, target_date: date) -> list[TimeSlot]:
        """Toate sloturile dintr-o zi (active + inactive), cu programarile incluse."""
        return (
            self.db.query(TimeSlot)
            .options(joinedload(TimeSlot.appointments))
            .filter(TimeSlot.date == target_date)
            .order_by(TimeSlot.start_time)
            .all()
        )

    def get_available(self, target_date: date) -> list[TimeSlot]:
        """Sloturile libere dintr-o zi (active si nerezervate)."""
        all_slots = self.get_by_date(target_date)
        return [s for s in all_slots if s.is_active and not s.is_booked()]

    def exists(self, target_date: date, start_time: time) -> bool:
        """Verifica daca exista deja un slot la data+ora data."""
        return (
            self.db.query(TimeSlot)
            .filter(TimeSlot.date == target_date, TimeSlot.start_time == start_time)
            .first()
        ) is not None

    def get_by_date_and_frizer(self, target_date: date, frizer_id: int) -> list[TimeSlot]:
        """Toate sloturile dintr-o zi pentru un frizer specific (active + inactive)."""
        return (
            self.db.query(TimeSlot)
            .options(joinedload(TimeSlot.appointments))
            .filter(TimeSlot.date == target_date, TimeSlot.frizer_id == frizer_id)
            .order_by(TimeSlot.start_time)
            .all()
        )

    def get_available_by_frizer(self, target_date: date, frizer_id: int) -> list[TimeSlot]:
        """Sloturile libere dintr-o zi pentru un frizer specific (active si nerezervate)."""
        all_slots = self.get_by_date_and_frizer(target_date, frizer_id)
        return [s for s in all_slots if s.is_active and not s.is_booked()]
