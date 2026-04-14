from datetime import date as date_type
from datetime import time as time_type
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator, ConfigDict
from models import AppointmentStatus


# ── Base schemas ───────────────────────────────────────────────────────────
class AppointmentBase(BaseModel):
    client_name:  str
    client_phone: str
    service_id:   int
    date:         date_type
    start_time:   time_type

    @field_validator("client_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Numele nu poate fi gol.")
        return v.strip()

    @field_validator("client_phone")
    @classmethod
    def phone_valid(cls, v: str) -> str:
        digits = v.replace(" ", "").replace("-", "").replace("+", "")
        if not digits.isdigit() or len(digits) < 9:
            raise ValueError("Numarul de telefon nu este valid.")
        return v.strip()


# ── Create / Update ────────────────────────────────────────────────────────
class AppointmentCreate(AppointmentBase):
    """Schema primita la crearea unei programari (POST /book)."""
    frizer_id: Optional[int] = None


class AppointmentUpdate(BaseModel):
    """Schema pentru modificarea unei programari de catre admin."""
    date:       Optional[date_type]         = None
    start_time: Optional[time_type]         = None
    status:     Optional[AppointmentStatus] = None


# ── Read (raspuns catre client) ────────────────────────────────────────────
class AppointmentRead(AppointmentBase):
    """Schema returnata in raspunsurile API."""
    model_config = ConfigDict(from_attributes=True)

    id:         int
    status:     AppointmentStatus
    created_at: datetime


# ── TimeSlot ───────────────────────────────────────────────────────────────
class TimeSlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    date:       date_type
    start_time: time_type
    is_active:  bool
    is_booked:  bool  # calculat din relatia appointments


# ── Service ────────────────────────────────────────────────────────────────
class ServiceRead(BaseModel):
    """Schema pentru citirea serviciilor."""
    model_config = ConfigDict(from_attributes=True)

    id:          int
    name:        str
    description: Optional[str]
    price:       Optional[int]
    frizer_id:   int
