from datetime import date, time
from typing import Optional
from sqlalchemy.orm import Session
from models import Appointment, AppointmentStatus
from repositories.appointment_repository import AppointmentRepository
from repositories.slot_repository import SlotRepository
from schemas import AppointmentCreate, AppointmentUpdate


class AppointmentService:
    """
    Logica de business pentru programari.
    Valideaza disponibilitatea inainte de creare
    si aplica regulile de business la modificari.
    """

    def __init__(self, db: Session) -> None:
        self.repo  = AppointmentRepository(db)
        self.slots = SlotRepository(db)

    def create(self, data: AppointmentCreate) -> Appointment:
        """
        Creeaza o programare dupa ce verifica:
        - slotul exista si este activ
        - slotul nu este deja ocupat
        - slotul este pentru frizerul corect
        """
        slot = self._get_slot_or_raise(data.date, data.start_time, data.frizer_id)

        appointment = Appointment(
            client_name=data.client_name,
            client_phone=data.client_phone,
            service_id=data.service_id,
            date=data.date,
            start_time=data.start_time,
            status=AppointmentStatus.CONFIRMED,
            slot_id=slot.id,
            frizer_id=data.frizer_id,
        )
        return self.repo.create(appointment)

    def update(self, appointment_id: int, data: AppointmentUpdate) -> Appointment:
        """Modifica ora sau statusul unei programari existente."""
        appointment = self._get_or_raise(appointment_id)

        if data.date or data.start_time:
            new_date = data.date or appointment.date
            new_time = data.start_time or appointment.start_time
            slot = self._get_slot_or_raise(new_date, new_time, appointment.frizer_id)
            appointment.date       = new_date
            appointment.start_time = new_time
            appointment.slot_id    = slot.id

        if data.status:
            appointment.status = data.status

        return self.repo.update(appointment)

    def cancel(self, appointment_id: int) -> Appointment:
        appointment = self._get_or_raise(appointment_id)
        return self.repo.cancel(appointment)

    def get_by_date(self, target_date: date) -> list[Appointment]:
        return self.repo.get_by_date(target_date)

    def get_by_date_and_frizer(self, target_date: date, frizer_id: int) -> list[Appointment]:
        """Programarile dintr-o zi pentru un frizer specific."""
        return self.repo.get_by_date_and_frizer(target_date, frizer_id)

    # ── Helpers private ────────────────────────────────────────
    def _get_or_raise(self, appointment_id: int) -> Appointment:
        appointment = self.repo.get_by_id(appointment_id)
        if not appointment:
            raise ValueError(f"Programarea #{appointment_id} nu exista.")
        return appointment

    def _get_slot_or_raise(self, target_date: date, start_time: time, frizer_id: int):
        """Cauta slotul pentru data, ora SI frizer specifici."""
        slot = (
            self.slots.db.query(__import__("models").TimeSlot)
            .filter_by(date=target_date, start_time=start_time, frizer_id=frizer_id)
            .first()
        )
        if not slot:
            raise ValueError("Ora selectata nu este disponibila.")
        if not slot.is_active:
            raise ValueError("Ora selectata este blocata.")
        if slot.is_booked():
            raise ValueError("Ora selectata este deja rezervata.")
        return slot
