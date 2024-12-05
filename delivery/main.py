import threading

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import engine, SessionLocal
from rabbitmq import send_delivery, listen_queue_started_delivery, completed_delivery
from schemas import DeliveryCreate
from models import Orders, DeliveryStatuses, get_datetime_now, Base


app = FastAPI()
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    listener_thread = threading.Thread(target=listen_queue_started_delivery, daemon=True)
    listener_thread.start()

@app.post("/creating_delivery", response_model=DeliveryCreate)
async def create_delivery(delivery_data: DeliveryCreate, db: Session = Depends(get_db)):
    if delivery_data.is_pickup:
        raise HTTPException(status_code=400, detail="Pickup does not require a courier")
    delivery = Orders(
        customer=delivery_data.customer,
        address=delivery_data.address,
        start_time= get_datetime_now(),
        is_pickup= delivery_data.is_pickup,
        status=DeliveryStatuses.created
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    send_delivery(delivery)
    return delivery

@app.get("/creating_delivery/{id}")
async def get_delivery(id: int, db: Session = Depends(get_db)):
    delivery = db.query(Orders).filter(Orders.id_order == id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Order was not found")
    return delivery

@app.patch("/creating_delivery/{id}/start")
async def start_delivery(id: int, db: Session = Depends(get_db)):
    delivery = db.query(Orders).filter(Orders.id_order == id).first()
    if not delivery or delivery.status != DeliveryStatuses.accepted:
        raise HTTPException(status_code=400, detail="Order cannot be started")
    delivery.status = DeliveryStatuses.started
    delivery.start_time = datetime.now()
    db.commit()
    return delivery

@app.patch("/creating_delivery/{id}/complete")
async def complete_delivery(id: int, db: Session = Depends(get_db)):
    delivery = db.query(Orders).filter(Orders.id_order == id).first()
    if not delivery or delivery.status != DeliveryStatuses.started:
        raise HTTPException(status_code=400, detail="Order cannot be completed")
    delivery.status = DeliveryStatuses.completed
    delivery.end_time = datetime.now()
    db.commit()
    if delivery.courier_id:
        completed_delivery(delivery.courier_id)
    return delivery

@app.patch("/creating_delivery/{id}/cancel")
async def cancel_delivery(id: int, db: Session = Depends(get_db)):
    delivery = db.query(Orders).filter(Orders.id_order == id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Order was not found")
    if delivery.status == DeliveryStatuses.completed:
        raise HTTPException(status_code=400, detail="A completed order cannot be cancelled")
    delivery.status = DeliveryStatuses.canceled
    delivery.end_time = datetime.now()
    db.commit()
    if delivery.courier_id:
        completed_delivery(delivery.courier_id)
    return delivery