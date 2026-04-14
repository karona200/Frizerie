from datetime import date, time
from sqlalchemy.orm import Session
from models import WorkingHours, WorkingHoursOverride, Frizer, TimeSlot
from repositories.working_hours_repository import WorkingHoursRepository
from config import config


class WorkingHoursService:
    """
    Logica de business pentru orarul frizerului.
    La prima pornire populeaza zilele cu valorile din config.py.
    """

    def __init__(self, db: Session) -> None:
        self.repo = WorkingHoursRepository(db)
        self.db = db

    def seed_defaults(self) -> None:
        """
        Populeaza tabelul cu orarul implicit din config 
        pentru toti frizerii care nu au program inregistrat.
        """
        frizers = self.db.query(Frizer).all()
        
        if not frizers:
            print("  ℹ No frizers found, skipping schedule initialization")
            return
        
        default_start = time(config.working_hours_start, 0)
        default_end   = time(config.working_hours_end, 0)

        for frizer in frizers:
            # Check if this frizer already has working hours
            existing_wh = self.db.query(WorkingHours).filter_by(frizer_id=frizer.id).first()
            if existing_wh:
                continue  # Already initialized
            
            # Create default working hours for each weekday
            for weekday in range(7):
                is_active = weekday < 6  # Luni-Sambata activ, Duminica liber
                wh = WorkingHours(
                    frizer_id=frizer.id,
                    weekday=weekday,
                    start_time=default_start,
                    end_time=default_end,
                    is_active=is_active,
                )
                self.repo.create(wh)
            
            print(f"  ✓ Initialized schedule for: {frizer.name}")

    def get_all(self) -> list[WorkingHours]:
        return self.repo.get_all_ordered()

    def get_all_for_frizer(self, frizer_id: int) -> list[WorkingHours]:
        """Get all working hours for a specific frizer, ordered by weekday"""
        return self.db.query(WorkingHours).filter_by(frizer_id=frizer_id).order_by(WorkingHours.weekday).all()

    def get_for_weekday(self, weekday: int, frizer_id: int | None = None) -> WorkingHours | None:
        """Get working hours for a specific weekday, optionally filtered by frizer"""
        query = self.db.query(WorkingHours).filter_by(weekday=weekday)
        if frizer_id:
            query = query.filter_by(frizer_id=frizer_id)
        return query.first()

    def get_override_for_date(self, target_date: date, frizer_id: int | None = None) -> WorkingHoursOverride | None:
        """Get override for a specific date, optionally filtered by frizer"""
        query = self.db.query(WorkingHoursOverride).filter_by(date=target_date)
        if frizer_id:
            query = query.filter_by(frizer_id=frizer_id)
        return query.first()

    def get_all_overrides(self, frizer_id: int | None = None) -> list[WorkingHoursOverride]:
        """Get all overrides, optionally filtered by frizer"""
        query = self.db.query(WorkingHoursOverride)
        if frizer_id:
            query = query.filter_by(frizer_id=frizer_id)
        return query.order_by(WorkingHoursOverride.date).all()

    def update_override(
        self,
        target_date: date,
        start_time:  time,
        end_time:    time,
        is_active:   bool,
        frizer_id:   int | None = None,
    ) -> WorkingHoursOverride:
        if end_time <= start_time:
            raise ValueError("Ora de sfarsit trebuie sa fie dupa ora de inceput.")

        # Clear existing slots for this date/frizer so they get regenerated
        self.db.query(TimeSlot).filter_by(
            date=target_date,
            frizer_id=frizer_id
        ).delete()

        override = self.get_override_for_date(target_date, frizer_id)
        if not override:
            override = WorkingHoursOverride(
                date=target_date,
                start_time=start_time,
                end_time=end_time,
                is_active=is_active,
                frizer_id=frizer_id,
            )
            return self.repo.create(override)

        override.start_time = start_time
        override.end_time   = end_time
        override.is_active  = is_active
        return self.repo.update(override)

    def delete_override(self, target_date: date, frizer_id: int | None = None) -> None:
        # Clear existing slots for this date/frizer so they get regenerated with default schedule
        self.db.query(TimeSlot).filter_by(
            date=target_date,
            frizer_id=frizer_id
        ).delete()
        
        override = self.get_override_for_date(target_date, frizer_id)
        if override:
            self.repo.delete(override)

    def update_day(
        self,
        weekday:    int,
        start_time: time,
        end_time:   time,
        is_active:  bool,
        frizer_id:  int | None = None,
    ) -> WorkingHours:
        if end_time <= start_time:
            raise ValueError("Ora de sfarsit trebuie sa fie dupa ora de inceput.")

        wh = self.get_for_weekday(weekday, frizer_id)
        if not wh:
            raise ValueError(f"Ziua {weekday} nu exista in baza de date pentru frizer_id={frizer_id}.")

        wh.start_time = start_time
        wh.end_time   = end_time
        wh.is_active  = is_active
        return self.repo.update(wh)
