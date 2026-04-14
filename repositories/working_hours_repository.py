from datetime import date
from models import WorkingHours, WorkingHoursOverride
from repositories.base import BaseRepository


class WorkingHoursRepository(BaseRepository[WorkingHours]):
    """Operatii DB pentru orarul de lucru."""

    model = WorkingHours

    def get_by_weekday(self, weekday: int) -> WorkingHours | None:
        return (
            self.db.query(WorkingHours)
            .filter(WorkingHours.weekday == weekday)
            .first()
        )

    def get_all_ordered(self) -> list[WorkingHours]:
        """Toate zilele ordonate Luni → Duminica."""
        return (
            self.db.query(WorkingHours)
            .order_by(WorkingHours.weekday)
            .all()
        )

    def get_override_by_date(self, target_date: date) -> WorkingHoursOverride | None:
        return (
            self.db.query(WorkingHoursOverride)
            .filter(WorkingHoursOverride.date == target_date)
            .first()
        )

    def get_all_overrides_ordered(self) -> list[WorkingHoursOverride]:
        return (
            self.db.query(WorkingHoursOverride)
            .order_by(WorkingHoursOverride.date)
            .all()
        )

    def get_by_weekday_and_frizer(self, weekday: int, frizer_id: int) -> WorkingHours | None:
        """Get working hours for a specific weekday and frizer."""
        return (
            self.db.query(WorkingHours)
            .filter(WorkingHours.weekday == weekday, WorkingHours.frizer_id == frizer_id)
            .first()
        )

    def get_override_by_date_and_frizer(self, target_date: date, frizer_id: int) -> WorkingHoursOverride | None:
        """Get override for a specific date and frizer."""
        return (
            self.db.query(WorkingHoursOverride)
            .filter(WorkingHoursOverride.date == target_date, WorkingHoursOverride.frizer_id == frizer_id)
            .first()
        )
