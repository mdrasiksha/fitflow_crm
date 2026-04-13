from sqlalchemy import Column, Integer, String, Date, ForeignKey
from database import Base

# CLIENT TABLE
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)
    goal = Column(String)
    start_date = Column(Date)
    status = Column(String, default="active")  # active / at_risk


# CHECK-IN TABLE
class Checkin(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    date = Column(Date)
    status = Column(String)  # yes / no / missed


# PAYMENT TABLE (optional)
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    amount = Column(Integer)
    status = Column(String)  # paid / pending
    due_date = Column(Date)