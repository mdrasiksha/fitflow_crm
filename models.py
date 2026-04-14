from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    goal = Column(String, nullable=False)
    start_date = Column(Date)
    status = Column(String, default="active")  # active / at_risk

    checkins = relationship("Checkin", back_populates="client", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="client", cascade="all, delete-orphan")


class Checkin(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String, nullable=False)  # yes / no / missed

    client = relationship("Client", back_populates="checkins")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    amount = Column(Integer)
    status = Column(String)  # paid / pending
    due_date = Column(Date)

    client = relationship("Client", back_populates="payments")
