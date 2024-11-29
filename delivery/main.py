import threading

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import engine, SessionLocal
from models import Orders, DeliveryStatuses, DeliveryCreate, get_datetime_now, Base
import pika
import json

app = FastAPI()
#models.Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

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

def send_order_created_message(order_id: int):
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    channel.queue_declare(queue='savitskiy_order_created', durable=True)

    message = json.dumps({"order_id": order_id})
    channel.basic_publish(
        exchange='',
        routing_key='savitskiy_order_created',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        )
    )
    print(f"Заказ {order_id} отправлен на RabbitMQ.")
    connection.close()

@app.post("/creating_delivery")
def create_delivery(delivery_data: DeliveryCreate, db: Session = Depends(get_db)):
    if delivery_data.is_pickup:
        raise HTTPException(status_code=400, detail="Самовывоз не требует курьера")
    delivery = Orders(
        customer=delivery_data.customer,
        address=delivery_data.address,
        start_time= get_datetime_now(),
        is_pickup= delivery_data.is_pickup,
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    send_order_created_message(delivery.id_order)

    return delivery

@app.get("/creating_delivery/{id}")
def get_delivery(id: int, db: Session = Depends(get_db)):
    delivery = db.query(Orders).filter(Orders.id_order == id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return delivery

@app.patch("/creating_delivery/{id}/accept")
def accept_delivery(id: int, db: Session = Depends(get_db)):
    delivery = db.query(Orders).filter(Orders.id_order == id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    delivery.status = DeliveryStatuses.accepted
    #delivery.courier_id = courier_id
    db.commit()
    return delivery

@app.patch("/creating_delivery/{id}/start")
def start_delivery(id: int, db: Session = Depends(get_db)):
    delivery = db.query(Orders).filter(Orders.id_order == id).first()
    if not delivery or delivery.status != DeliveryStatuses.accepted:
        raise HTTPException(status_code=400, detail="Заказ не может быть начат")
    delivery.status = DeliveryStatuses.started
    delivery.start_time = datetime.now()
    db.commit()
    return delivery

@app.patch("/creating_delivery/{id}/complete")
def complete_delivery(id: int, db: Session = Depends(get_db)):
    delivery = db.query(Orders).filter(Orders.id_order == id).first()
    if not delivery or delivery.status != DeliveryStatuses.started:
        raise HTTPException(status_code=400, detail="Заказ не может быть завершен")
    delivery.status = DeliveryStatuses.completed
    delivery.end_time = datetime.now()
    db.commit()
    return delivery

@app.patch("/creating_delivery/{id}/cancel")
def cancel_delivery(id: int, db: Session = Depends(get_db)):
    delivery = db.query(Orders).filter(Orders.id_order == id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if delivery.status == DeliveryStatuses.completed:
        raise HTTPException(status_code=400, detail="Завершенный заказ не может быть отменен")
    delivery.status = DeliveryStatuses.canceled
    db.commit()
    return delivery

def on_courier_assigned(ch, method, properties, body):
    message = json.loads(body)
    order_id = message["order_id"]
    courier_id = message["courier_id"]
    print(f"Курьер {courier_id} принял заказ {order_id}")

    db = SessionLocal()
    order = db.query(Orders).filter(Orders.id_order == order_id).first()
    if order:
        order.courier_id = courier_id
        db.commit()
        db.close()

def start_listening_for_courier_assignments():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue='courier_assigned', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='courier_assigned', on_message_callback=on_courier_assigned)
    print("Ожидание принятия курьером...")
    channel.start_consuming()

courier_listener_thread = threading.Thread(target=start_listening_for_courier_assignments)
courier_listener_thread.start()