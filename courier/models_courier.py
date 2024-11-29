import uuid

from sqlalchemy import Column, Integer, String, Enum
from enum import Enum as PyEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from database_courier import engine
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class DeliveryManStatuses(PyEnum):
    available = "available"
    busy = "busy"
    off_shift = "not_working"

class DeliveryMan(Base):
    __tablename__ = "delivery_man"

    courier_id = Column(Integer, primary_key=True, autoincrement=True)
    fio_courier = Column(String, nullable=False)
    status = Column(Enum(DeliveryManStatuses), default=DeliveryManStatuses.off_shift)

SessionLocal = sessionmaker(bind=engine)
