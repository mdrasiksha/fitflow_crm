from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models
from datetime import date
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ======================
# DB Dependency
# ======================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ======================
# Pydantic Models
# ======================

class ClientCreate(BaseModel):
    name: str
    phone: str
    goal: str


class CheckinCreate(BaseModel):
    client_id: int
    status: str  # "yes" or "no"


# ======================
# CLIENT APIs
# ======================

# Add Client
@app.post("/clients")
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    new_client = models.Client(
        name=client.name,
        phone=client.phone,
        goal=client.goal,
        start_date=date.today(),
        status="active"
    )

    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    return {"message": "Client added", "client_id": new_client.id}


# Get All Clients
@app.get("/clients")
def get_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).all()


# ======================
# CHECK-IN API
# ======================

@app.post("/checkin")
def create_checkin(data: CheckinCreate, db: Session = Depends(get_db)):
    new_checkin = models.Checkin(
        client_id=data.client_id,
        date=date.today(),
        status=data.status
    )

    db.add(new_checkin)
    db.commit()

    return {"message": "Check-in recorded"}


# ======================
# BUSINESS LOGIC
# ======================

# Calculate streak
def calculate_streak(client_id: int, db: Session):
    checkins = db.query(models.Checkin)\
        .filter(models.Checkin.client_id == client_id)\
        .order_by(models.Checkin.date.desc())\
        .all()

    streak = 0

    for c in checkins:
        if c.status == "yes":
            streak += 1
        else:
            break

    return streak


# Detect at-risk clients
def is_at_risk(client_id: int, db: Session):
    checkins = db.query(models.Checkin)\
        .filter(models.Checkin.client_id == client_id)\
        .order_by(models.Checkin.date.desc())\
        .limit(2)\
        .all()

    missed_days = sum(1 for c in checkins if c.status != "yes")

    return missed_days >= 2


# ======================
# DASHBOARD API
# ======================

@app.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    clients = db.query(models.Client).all()

    result = []

    for client in clients:
        streak = calculate_streak(client.id, db)
        at_risk = is_at_risk(client.id, db)

        result.append({
            "id": client.id,
            "name": client.name,
            "goal": client.goal,
            "streak": streak,
            "status": "at_risk" if at_risk else "active"
        })

    return result