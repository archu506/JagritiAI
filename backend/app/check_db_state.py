import sys
from app.db.session import SessionLocal
from app.models.user import User
from app.models.awareness import Alert

db = SessionLocal()
asha = db.query(User).filter(User.email == 'asha@demo.jagriti').first()
if asha:
    print(f"ASHA worker: id={asha.id}, email={asha.email}, role={asha.role}, active={asha.is_active}")
else:
    print("ASHA worker NOT FOUND")

alerts = db.query(Alert).all()
print(f"Total alerts: {len(alerts)}")
for a in alerts:
    print(f"Alert ID={a.id}, cat={a.topic_category}, tag={a.topic_tag}, block={a.geo_block_id}, assigned_asha_id={a.assigned_asha_id}, status={a.verification_status}, assigned_at={a.assigned_at}, assigned_by={a.assigned_by}")
