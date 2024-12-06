from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from enum import Enum as PyEnum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

class DeliveryStatuses(PyEnum):
    created = "created"
    accepted = "accepted"
    started = "started"
    completed = "completed"
    canceled = "canceled"
    pickup_selected = "pickup_selected"

def get_datetime_now():
    return datetime.now()

class Orders(Base):
    __tablename__ = 'orders'

    id_order = Column(Integer, primary_key=True, autoincrement=True)
    customer = Column(String, nullable=False)
    address = Column(String, nullable=False)
    start_time = Column(DateTime, default=get_datetime_now)
    end_time = Column(DateTime)
    status = Column(Enum(DeliveryStatuses), default=DeliveryStatuses.created)
    courier_id = Column(Integer)
    is_pickup = Column(Boolean, default=False)