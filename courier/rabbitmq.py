import json
import random

import pika

from models_courier import DeliveryMan, DeliveryManStatuses
from database_courier import SessionLocal

RABBITMQ_HOST = "51.250.26.59"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "guest"
RABBITMQ_PASSWORD = "guest123"
DELIVERY_QUEUE_NAME = "start_delivery_queue_savitskiy"

def callback(ch, method, properties, body):
  message = json.loads(body)
  id_order = message["id_order"]
  print(f"Received order - {id_order}")
  courier_id = assign_order_to_courier(id_order)
  if courier_id:
      print(f"Order {id_order} assigned to courier {courier_id}")
  else:
      print(f"Failed to assign courier for order {id_order}")

def listen_queue_start_delivery():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(DELIVERY_QUEUE_NAME, durable=True)
    channel.basic_consume(
        queue=DELIVERY_QUEUE_NAME, on_message_callback=callback, auto_ack=True
    )
    print("Log: Reading a message from a queue start_delivery_queue_savitskiy")
    channel.start_consuming()


def assign_order_to_courier(order_id):
    db = SessionLocal()
    try:
        available_couriers = db.query(DeliveryMan).filter(
            DeliveryMan.status == DeliveryManStatuses.available
        ).all()

        if not available_couriers:
            print(f"No available couriers for order {order_id}")
            return None
        selected_courier = random.choice(available_couriers)
        selected_courier.status = DeliveryManStatuses.busy
        db.commit()
        print(
            f"Assigned order {order_id} to courier {selected_courier.fio_courier} (ID: {selected_courier.courier_id})")

        return selected_courier.courier_id
    finally:
        db.close()