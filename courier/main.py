import threading
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from utility import initialize_delivery_man
from rabbitmq import listen_queue_start_delivery, listen_queue_completed_delivery
from models_courier import DeliveryMan, DeliveryManStatuses, Base
from database_courier import SessionLocal, engine

app = FastAPI()

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


initialize_delivery_man(SessionLocal())

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    listener_thread_for_start_delivery = threading.Thread(target=listen_queue_start_delivery, daemon=True)
    listener_thread_for_start_delivery.start()
    listener_thread_for_completed_delivery = threading.Thread(target=listen_queue_completed_delivery, daemon=True)
    listener_thread_for_completed_delivery.start()

@app.get("/couriers")
async def get_couriers(db: Session = Depends(get_db)):
    couriers = db.query(DeliveryMan).all()
    return couriers

@app.get("/courier/{id}")
async def get_courier(id: int, db: Session = Depends(get_db)):
    courier = db.query(DeliveryMan).filter(DeliveryMan.courier_id == id).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    return courier

@app.patch("/courier/{id}/activate")
async def activate_courier(id: int, db: Session = Depends(get_db)):
    courier = db.query(DeliveryMan).filter(DeliveryMan.courier_id == id).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    if courier.status == DeliveryManStatuses.busy or courier.status == DeliveryManStatuses.available:
        raise HTTPException(
            status_code=400,
            detail="Вы не можете начать смену, вы уже работаете"
        )
    courier.status = DeliveryManStatuses.available
    db.commit()
    return {"message": f"Курьер {id} готов вкалывать"}

@app.patch("/courier/{id}/deactivate")
async def deactivate_courier(id: int, db: Session = Depends(get_db)):
    courier = db.query(DeliveryMan).filter(DeliveryMan.courier_id == id).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    if courier.status == DeliveryManStatuses.busy:
        raise HTTPException(
            status_code=400,
            detail="Вы не можете закончить смену, пока не завершите заказ!"
        )
    courier.is_active = False
    db.commit()
    return {"message": f"Курьер {id} закончил смену"}