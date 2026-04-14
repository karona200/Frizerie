from __future__ import annotations
from datetime import date, time, datetime
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import String, Date, Time, DateTime, Integer, Boolean, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


# ── Enum-uri ───────────────────────────────────────────────────────────────
class AppointmentStatus(str, PyEnum):
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


# ── Modele ─────────────────────────────────────────────────────────────────
class Appointment(Base):
    """
    Reprezinta o programare facuta de un client.

    Relatii:
        - Appointment.slot_id → TimeSlot.id  (many-to-one)
    """
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Date client
    client_name:  Mapped[str] = mapped_column(String(100), nullable=False)
    client_phone: Mapped[str] = mapped_column(String(20),  nullable=False)

    # Detalii programare
    date:         Mapped[date] = mapped_column(Date,         nullable=False, index=True)
    start_time:   Mapped[time] = mapped_column(Time,         nullable=False)

    # Status
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus),
        default=AppointmentStatus.CONFIRMED,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relatii
    slot_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("time_slots.id"), nullable=True
    )
    slot: Mapped["TimeSlot"] = relationship("TimeSlot", back_populates="appointments")
    
    frizer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("frizer.id"), nullable=True
    )
    frizer: Mapped["Frizer"] = relationship("Frizer")
    
    service_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("services.id"), nullable=True
    )
    service_rel: Mapped["Service"] = relationship("Service")

    def __repr__(self) -> str:
        return (
            f"<Appointment id={self.id} client={self.client_name!r} "
            f"date={self.date} time={self.start_time} status={self.status}>"
        )

class Description(Base):
    """
    Reprezinta o descriere a frizerului, vizibila pe pagina principala."""

    __tablename__ = "description"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String(1000), nullable=False)

    def __repr__(self) -> str:
        return f"<Description id={self.id} content={self.content[:50]!r}...>"
    
class Frizer(Base):
    """
    Reprezinta un frizer, cu nume si descriere.
    Poate fi extins in viitor pentru programari multiple, specializari etc.
    """

    __tablename__ = "frizer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


    def __repr__(self) -> str:
        return f"<Frizer id={self.id} name={self.name!r}>"


class Service(Base):
    """
    Reprezinta un serviciu oferit de un frizer (tuns, barba, etc.)
    """

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Price in lei, optional
    frizer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("frizer.id"), nullable=False, index=True
    )
    frizer: Mapped["Frizer"] = relationship("Frizer")

    def __repr__(self) -> str:
        return f"<Service id={self.id} name={self.name!r} price={self.price}>"


class TimeSlot(Base):
    """
    Reprezinta un interval orar disponibil intr-o zi pentru un frizer.

    Un TimeSlot poate fi:
        - activ  → disponibil pentru rezervare
        - inactiv → blocat de frizer (concediu, pauza etc.)

    Relatii:
        - TimeSlot.appointments → lista de Appointment
        - TimeSlot.frizer_id → Frizer.id
    """
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    date:       Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_active:  Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Frizer
    frizer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("frizer.id"), nullable=False, index=True
    )
    frizer: Mapped["Frizer"] = relationship("Frizer")

    # Relatii
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="slot"
    )

    def is_booked(self) -> bool:
        """Returneaza True daca slotul are cel putin o programare activa."""
        return any(
            a.status != AppointmentStatus.CANCELLED
            for a in self.appointments
        )

    def __repr__(self) -> str:
        return (
            f"<TimeSlot id={self.id} date={self.date} "
            f"time={self.start_time} active={self.is_active}>"
        )


# ── Zile saptamana ─────────────────────────────────────────────────────────
DAYS_RO = {
    0: "Luni",
    1: "Marti",
    2: "Miercuri",
    3: "Joi",
    4: "Vineri",
    5: "Sambata",
    6: "Duminica",
}


class WorkingHours(Base):
    """
    Orarul de lucru al frizerului per zi a saptamanii.

    weekday: 0=Luni, 1=Marti, ..., 6=Duminica
    Daca is_active=False, frizerul nu lucreaza in ziua respectiva.
    Un frizer pe zi (weekday + frizer_id = unic)
    """
    __tablename__ = "working_hours"

    id:         Mapped[int]  = mapped_column(Integer, primary_key=True, index=True)
    weekday:    Mapped[int]  = mapped_column(Integer, nullable=False)  # 0-6
    start_time: Mapped[time] = mapped_column(Time,    nullable=False)
    end_time:   Mapped[time] = mapped_column(Time,    nullable=False)
    is_active:  Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Frizer
    frizer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("frizer.id"), nullable=False, index=True
    )
    frizer: Mapped["Frizer"] = relationship("Frizer")

    @property
    def day_name(self) -> str:
        return DAYS_RO.get(self.weekday, "Necunoscut")

    def __repr__(self) -> str:
        return (
            f"<WorkingHours {self.day_name} "
            f"{self.start_time}-{self.end_time} active={self.is_active}>"
        )


class WorkingHoursOverride(Base):
    """
    Orarul de lucru pentru o data explicita de un frizer (zile libere).

    Folosit pentru exceptii care se aplica doar unei date concrete,
    fara a modifica orarul saptamanal implicit.
    """
    __tablename__ = "working_hours_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Frizer
    frizer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("frizer.id"), nullable=False, index=True
    )
    frizer: Mapped["Frizer"] = relationship("Frizer")

    def __repr__(self) -> str:
        return (
            f"<WorkingHoursOverride {self.date} "
            f"{self.start_time}-{self.end_time} active={self.is_active}>"
        )
