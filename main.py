from datetime import date
from typing import Generator, Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

import models
from database import Base, SessionLocal, engine
from streaks import calculate_streak

app = FastAPI(title="FitFlow CRM API", version="1.0.0")

# CORS (safe defaults for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables
Base.metadata.create_all(bind=engine)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
        },
    )


# ======================
# DB Dependency
# ======================
def get_db() -> Generator[Session, None, None]:
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
    status: Literal["yes", "no"]


# ======================
# Business Logic
# ======================
def is_at_risk(client: models.Client) -> bool:
    return calculate_inactive_days(client) >= 2


def calculate_inactive_days(client: models.Client) -> int:
    checkins = sorted(client.checkins, key=lambda c: c.date, reverse=True)
    if checkins:
        last_checkin_date = checkins[0].date
    else:
        last_checkin_date = client.start_date or date.today()

    return max((date.today() - last_checkin_date).days, 0)


def dashboard_row(client: models.Client) -> dict:
    inactive_days = calculate_inactive_days(client)
    at_risk = is_at_risk(client)
    return {
        "id": client.id,
        "name": client.name,
        "goal": client.goal,
        "streak": calculate_streak(client),
        "status": "at_risk" if at_risk else "active",
        "inactive_days": inactive_days,
    }


# ======================
# Client APIs
# ======================
@app.post("/clients")
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    new_client = models.Client(
        name=client.name,
        phone=client.phone,
        goal=client.goal,
        start_date=date.today(),
        status="active",
    )

    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    return {
        "message": "Client added",
        "client_id": new_client.id,
    }


@app.get("/clients")
def get_clients(db: Session = Depends(get_db)):
    clients = db.query(models.Client).all()
    data = [
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "goal": c.goal,
            "start_date": c.start_date.isoformat() if c.start_date else None,
            "status": c.status,
        }
        for c in clients
    ]
    return {"success": True, "data": data, "count": len(data)}


# ======================
# Check-in API
# ======================
@app.post("/checkin")
def create_checkin(payload: CheckinCreate, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.id == payload.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    new_checkin = models.Checkin(
        client_id=payload.client_id,
        date=date.today(),
        status=payload.status,
    )

    db.add(new_checkin)
    db.commit()


    return {
        "success": True,
        "message": "Check-in recorded",
        "data": {
            "client_id": payload.client_id,
            "status": payload.status,
        },
    }


# ======================
# Dashboard API
# ======================
@app.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    clients = (
        db.query(models.Client)
        .options(joinedload(models.Client.checkins))
        .order_by(models.Client.id.desc())
        .all()
    )

    result = [dashboard_row(client) for client in clients]
    return {
        "success": True,
        "data": result,
        "count": len(result),
    }
