from datetime import date
from sqlalchemy.orm import Session
from models import Appointment, AppointmentStatus
from repositories.base import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    """
    Toate operatiile cu baza de date legate de programari.
    Rutele nu ating niciodata DB direct — trec prin acest repository.
    """

    model = Appointment

    def get_by_date(self, target_date: date) -> list[Appointment]:
        """Toate programarile dintr-o zi, ordonate dupa ora."""
        return (
            self.db.query(Appointment)
            .filter(Appointment.date == target_date)
            .order_by(Appointment.start_time)
            .all()
        )

    def get_by_date_and_frizer(self, target_date: date, frizer_id: int) -> list[Appointment]:
        """Programarile dintr-o zi pentru un frizer specific."""
        return (
            self.db.query(Appointment)
            .filter(Appointment.date == target_date, Appointment.frizer_id == frizer_id)
            .order_by(Appointment.start_time)
            .all()
        )

    def get_active_by_date(self, target_date: date) -> list[Appointment]:
        """Programarile active (ne-anulate) dintr-o zi."""
        return (
            self.db.query(Appointment)
            .filter(
                Appointment.date == target_date,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .order_by(Appointment.start_time)
            .all()
        )

    def get_active_by_date_and_frizer(self, target_date: date, frizer_id: int) -> list[Appointment]:
        """Programarile active (ne-anulate) dintr-o zi pentru un frizer specific."""
        return (
            self.db.query(Appointment)
            .filter(
                Appointment.date == target_date,
                Appointment.frizer_id == frizer_id,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .order_by(Appointment.start_time)
            .all()
        )

    def cancel(self, appointment: Appointment) -> Appointment:
        """Anuleaza o programare existenta."""
        appointment.status = AppointmentStatus.CANCELLED
        return self.update(appointment)
