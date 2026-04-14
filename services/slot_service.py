from datetime import date, time, timedelta, datetime
from sqlalchemy.orm import Session
from models import TimeSlot
from repositories.slot_repository import SlotRepository
from repositories.working_hours_repository import WorkingHoursRepository
from config import config


class SlotService:
    """
    Logica de business pentru sloturile orare per frizer.
    Citeste orarul din WorkingHours (DB), nu din config.py.
    Sloturile sunt generate per frizer.
    """

    def __init__(self, db: Session) -> None:
        self.repo    = SlotRepository(db)
        self.wh_repo = WorkingHoursRepository(db)
        self.db = db

    def generate_slots_for_date(self, target_date: date, frizer_id: int) -> list[TimeSlot]:
        """
        Genereaza sloturile pentru o zi si un frizer conform orarului din DB.
        Daca ziua e marcata inactiva (liber) nu genereaza nimic.
        Daca sloturile exista deja, le returneaza pe cele existente.
        """
        existing = self.repo.get_by_date_and_frizer(target_date, frizer_id)
        if existing:
            return existing

        # Citeste mai intai un override pentru data respectiva si frizer
        wh = self.wh_repo.get_override_by_date_and_frizer(target_date, frizer_id)
        if not wh:
            weekday = target_date.weekday()
            wh = self.wh_repo.get_by_weekday_and_frizer(weekday, frizer_id)

        # Daca nu exista orar in DB sau ziua e libera → niciun slot
        if not wh or not wh.is_active:
            return []

        slots: list[TimeSlot] = []
        current = datetime.combine(target_date, wh.start_time)
        end     = datetime.combine(target_date, wh.end_time)

        while current < end:
            slot = TimeSlot(
                date=target_date,
                start_time=current.time(),
                frizer_id=frizer_id
            )
            slots.append(self.repo.create(slot))
            current += timedelta(minutes=config.slot_duration_minutes)

        return slots

    def get_available_slots(self, target_date: date, frizer_id: int) -> list[TimeSlot]:
        """Returneaza sloturile libere pentru un frizer, generandu-le daca e nevoie."""
        self.generate_slots_for_date(target_date, frizer_id)
        return self.repo.get_available_by_frizer(target_date, frizer_id)
