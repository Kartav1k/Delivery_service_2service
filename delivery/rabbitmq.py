import json

import pika

from utility import add_courier_to_delivery

RABBITMQ_HOST="51.250.26.59"
RABBITMQ_PORT=5672
RABBITMQ_USER='guest'
RABBITMQ_PASSWORD='guest123'
DELIVERY_QUEUE_NAME = "start_delivery_queue_savitskiy"
STARTED_DELIVERY_QUEUE_NAME = "started_delivery_queue_savitskiy"
COMPLETED_DELIVERY_QUEUE_NAME = "completed_delivery_queue_savitskiy"

# Публикация заказов на RabbitMQ в очереди start_delivery_queue_savitskiy

def publish_delivery(message: dict):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials
    ))
    channel = connection.channel()
    channel.queue_declare(DELIVERY_QUEUE_NAME, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=DELIVERY_QUEUE_NAME,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2
        )

    )
    print(f"Order {message['id_order']} has been sent to RabbitMQ in the queue start_delivery_queue_savitskiy", flush=True)
    channel.close()

def send_delivery(delivery_data):
    message = {
        "id_order": delivery_data.id_order,
        "customer": delivery_data.customer,
        "address": delivery_data.address,
        "courier_id": delivery_data.courier_id,
        "is_pickup": delivery_data.is_pickup,
        "status": delivery_data.status.value
    }
    publish_delivery(message)

#Прослушивание очереди started_delivery_queue_savitskiy на прием информации о курьере

def callback(ch, method, properties, body):
  message = json.loads(body)
  id_order = message["id_order"]
  courier_id = message["courier_id"]
  add_courier_to_delivery(id_order, courier_id)
  print(f"Order received - {id_order} accepted by courier - {courier_id}. Data is being changed")

def listen_queue_started_delivery():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(STARTED_DELIVERY_QUEUE_NAME, durable=True)
    channel.basic_consume(
        queue=STARTED_DELIVERY_QUEUE_NAME, on_message_callback=callback, auto_ack=True
    )
    print("Log: Reading a message from a queue started_delivery_queue_savitskiy", flush=True)
    channel.start_consuming()

# Отправка сигнала курьеру в очередь completed_delivery_queue_savitskiy что он может быть свободен

def completed_delivery(courier_id: int):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials
    ))
    channel = connection.channel()
    channel.queue_declare(COMPLETED_DELIVERY_QUEUE_NAME, durable=True)
    message = {"courier_id": courier_id}
    channel.basic_publish(
        exchange='',
        routing_key=COMPLETED_DELIVERY_QUEUE_NAME,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )
    print(f"ID of courier - {message['courier_id']} has been sent to RabbitMQ in the queue completed_delivery_queue_savitskiy",
          flush=True)
    channel.close()