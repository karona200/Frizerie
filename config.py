from dataclasses import dataclass, field
from typing import List


@dataclass
class AppConfig:
    # ── Aplicatie ──────────────────────────────────────────────
    app_name: str = "Frizer Online"
    app_version: str = "0.1.0"
    debug: bool = True

    # ── Baza de date ───────────────────────────────────────────
    database_url: str = "sqlite:///./barber.db"

    # ── Program de lucru ───────────────────────────────────────
    working_hours_start: int = 9    # 09:00
    working_hours_end: int = 18     # 18:00
    slot_duration_minutes: int = 30

    # ── Admin ──────────────────────────────────────────────────
    admin_password: str = "frizer2024"  # schimba inainte de deploy!

    # ── Servicii disponibile ───────────────────────────────────
    services: List[str] = field(default_factory=lambda: [
        "Tuns",
        "Tuns + Barba",
        "Barba",
        "Tuns Copii",
    ])


# Instanta globala — importata in tot proiectul
config = AppConfig()
