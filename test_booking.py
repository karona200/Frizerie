from datetime import date, timedelta
from database import SessionLocal
from services.slot_service import SlotService

# Get next monday
today = date.today()
days_until_monday = (7 - today.weekday()) % 7
if days_until_monday == 0:
    days_until_monday = 7
next_monday = today + timedelta(days=days_until_monday)

print(f'Today: {today} (weekday {today.weekday()})')
print(f'Next available day: {next_monday}')

# Test booking on monday
db = SessionLocal()
slot_service = SlotService(db)
slots = slot_service.get_available_slots(next_monday)
print(f'Sloturi pe {next_monday}: {len(slots)}')
for slot in slots[:5]:
    print(f'  - {slot}')

# List all active frizers
from models import Frizer
frizers = db.query(Frizer).all()
print(f'\nFrizeri in DB: {len(frizers)}')
for f in frizers:
    print(f'  - {f.name} (id={f.id})')

db.close()
