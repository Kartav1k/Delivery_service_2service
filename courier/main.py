import threading
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from models_courier import DeliveryMan, DeliveryManStatuses, Base
from database_courier import SessionLocal, engine
import pika
import json

app = FastAPI()

#Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)



def initialize_delivery_man(db: Session):
    predefined_delivery_men = [
        DeliveryMan(fio_courier="Иван Иванов", status=DeliveryManStatuses.available),
        DeliveryMan(fio_courier="Петр Петров", status=DeliveryManStatuses.available),
        DeliveryMan(fio_courier="Михаил Михайлов", status=DeliveryManStatuses.off_shift),
    ]
    for delivery_man in predefined_delivery_men:
        db.add(delivery_man)
    db.commit()

initialize_delivery_man(SessionLocal())

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_rabbitmq_connection():
    return pika.BlockingConnection(pika.ConnectionParameters(
        host='51.250.26.59',
        port=5672,
        credentials=pika.PlainCredentials('guest', 'guest123')
    ))

def on_order_created(ch, method, properties, body):
    message = json.loads(body)
    order_id = message["order_id"]
    print(f"Получен заказ {order_id}")
    db = SessionLocal()
    courier = db.query(DeliveryMan).filter(DeliveryMan.status == DeliveryManStatuses.available).first()

    if courier:
        courier.status = DeliveryManStatuses.busy
        db.commit()
        send_courier_assigned_message(order_id, courier.courier_id)

        db.close()
    else:
        print("Нет доступных курьеров :(")

def send_courier_assigned_message(order_id: int, courier_id: int):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue='courier_assigned', durable=True)
    message = json.dumps({"order_id": order_id, "courier_id": courier_id})
    channel.basic_publish(
        exchange='',
        routing_key='courier_assigned',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,
        )
    )
    print(f"Курьер {courier_id} принял заказ {order_id}.")
    connection.close()

def start_listening():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue='savitskiy_order_created', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='savitskiy_order_created', on_message_callback=on_order_created)

    print("Ожидание заказов...")
    channel.start_consuming()

import threading
order_listener_thread = threading.Thread(target=start_listening)
order_listener_thread.start()

@app.get("/couriers")
def get_couriers(db: Session = Depends(get_db)):
    couriers = db.query(DeliveryMan).all()
    return couriers

@app.get("/courier/{id}")
def get_courier(id: int, db: Session = Depends(get_db)):
    courier = db.query(DeliveryMan).filter(DeliveryMan.courier_id == id).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    return courier

@app.patch("/courier/{id}/activate")
def activate_courier(id: int, db: Session = Depends(get_db)):
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
def deactivate_courier(id: int, db: Session = Depends(get_db)):
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
