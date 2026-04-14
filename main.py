from datetime import date
from typing import Generator, Literal

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

import models
from database import Base, SessionLocal, engine

app = FastAPI(title="FitFlow CRM API", version="1.0.0")

# CORS (safe defaults for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "null",  # useful when opening index.html directly in some browsers
    ],
    allow_credentials=True,
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
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=30)
    goal: str = Field(min_length=2, max_length=200)


class CheckinCreate(BaseModel):
    client_id: int = Field(gt=0)
    status: Literal["yes", "no"]


# ======================
# Business Logic
# ======================
def calculate_streak(client: models.Client) -> int:
    streak = 0
    for checkin in sorted(client.checkins, key=lambda c: c.date, reverse=True):
        if checkin.status == "yes":
            streak += 1
        else:
            break
    return streak


def is_at_risk(client: models.Client) -> bool:
    last_two = sorted(client.checkins, key=lambda c: c.date, reverse=True)[:2]
    if len(last_two) < 2:
        return False

    missed_days = sum(1 for checkin in last_two if checkin.status != "yes")
    return missed_days >= 2


def dashboard_row(client: models.Client) -> dict:
    at_risk = is_at_risk(client)
    return {
        "id": client.id,
        "name": client.name,
        "goal": client.goal,
        "streak": calculate_streak(client),
        "status": "at_risk" if at_risk else "active",
    }


# ======================
# Client APIs
# ======================
@app.post("/clients", status_code=status.HTTP_201_CREATED)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    new_client = models.Client(
        name=client.name.strip(),
        phone=client.phone.strip(),
        goal=client.goal.strip(),
        start_date=date.today(),
        status="active",
    )

    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    return {
        "success": True,
        "message": "Client added successfully",
        "data": {
            "id": new_client.id,
            "name": new_client.name,
            "phone": new_client.phone,
            "goal": new_client.goal,
            "status": new_client.status,
        },
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
