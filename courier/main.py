import threading
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

from database_courier import engine
from utility_courier import initialize_delivery_man
from rabbitmq import listen_queue_start_delivery, listen_queue_completed_delivery
from models_courier import DeliveryMan, DeliveryManStatuses


app = FastAPI()

initialize_delivery_man()

@app.on_event("startup")
async def startup_event():
    listener_thread_for_start_delivery = threading.Thread(target=listen_queue_start_delivery, daemon=True)
    listener_thread_for_start_delivery.start()
    listener_thread_for_completed_delivery = threading.Thread(target=listen_queue_completed_delivery, daemon=True)
    listener_thread_for_completed_delivery.start()

@app.get("/couriers")
async def get_couriers():
    with Session(engine) as db:
        couriers = db.query(DeliveryMan).all()
        return couriers

@app.get("/courier/{id}")
async def get_courier(id: int):
    with Session(engine) as db:
        courier = db.query(DeliveryMan).filter(DeliveryMan.courier_id == id).first()
        if not courier:
            raise HTTPException(status_code=404, detail="Courier was not found")
        return courier

@app.patch("/courier/{id}/activate")
async def activate_courier(id: int):
    with Session(engine) as db:
        courier = db.query(DeliveryMan).filter(DeliveryMan.courier_id == id).first()
        if not courier:
            raise HTTPException(status_code=404, detail="Courier was not found")
        if courier.status in {DeliveryManStatuses.busy, DeliveryManStatuses.available}:
            raise HTTPException(
                status_code=400,
                detail="You can't start a shift, you're already working"
            )
        courier.status = DeliveryManStatuses.available
        db.commit()
        return {"message": f"Courier {id} is ready to work hard"}

@app.patch("/courier/{id}/deactivate")
async def deactivate_courier(id: int):
    with Session(engine) as db:
        courier = db.query(DeliveryMan).filter(DeliveryMan.courier_id == id).first()
        if not courier:
            raise HTTPException(status_code=404, detail="Courier was not found")
        if courier.status == DeliveryManStatuses.busy:
            raise HTTPException(
                status_code=400,
                detail="You can't finish your shift until you complete the order!"
            )
        courier.status = DeliveryManStatuses.not_working
        db.commit()
        return {"message": f"Courier {id} has finished his shift"}