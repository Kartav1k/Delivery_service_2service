import json
import pika

from utility import assign_order_to_courier, free_courier

RABBITMQ_HOST = "51.250.26.59"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "guest"
RABBITMQ_PASSWORD = "guest123"
DELIVERY_QUEUE_NAME = "start_delivery_queue_savitskiy"
STARTED_DELIVERY_QUEUE_NAME = "started_delivery_queue_savitskiy"
COMPLETED_DELIVERY_QUEUE_NAME = "completed_delivery_queue_savitskiy"

# Прослушивание очереди заказов для назначение заказу курьера

def callback(ch, method, properties, body):
  message = json.loads(body)
  id_order = message["id_order"]
  print(f"Received order - {id_order}")
  courier_id = assign_order_to_courier(id_order)
  if courier_id:
      print(f"Order {id_order} assigned to courier {courier_id}", flush=True)
      send_changed_data_of_started_delivery(id_order, courier_id)

  else:
      print(f"There are no couriers available to order {id_order}", flush=True)

def listen_queue_start_delivery():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(DELIVERY_QUEUE_NAME, durable=True)
    channel.basic_consume(
        queue=DELIVERY_QUEUE_NAME, on_message_callback=callback, auto_ack=True
    )
    print("Log: Reading a message from a queue start_delivery_queue_savitskiy", flush=True)
    channel.start_consuming()

# Отправка данных курьера в очередь started_delivery_queue_savitskiy для таблицы заказов

def started_delivery(message: dict):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials
    ))
    channel = connection.channel()
    channel.queue_declare(STARTED_DELIVERY_QUEUE_NAME, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=STARTED_DELIVERY_QUEUE_NAME,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2
        )

    )
    print(f"Order {message['id_order']} has been sent to RabbitMQ in the queue started_delivery_queue_savitskiy", flush=True)
    channel.close()


def send_changed_data_of_started_delivery(id_order, courier_id):
    message = {
        "id_order": id_order,
        "courier_id": courier_id,
    }
    started_delivery(message)

# Прослушивание очереди выполненных заказов для освобождения курьера из рабства(временно)

def callback_completed_delivery(ch, method, properties, body):
  message = json.loads(body)
  courier_id = message["courier_id"]
  print(f"Received ID of courier - {courier_id}")
  free_courier(courier_id)

def listen_queue_completed_delivery():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(COMPLETED_DELIVERY_QUEUE_NAME, durable=True)
    channel.basic_consume(
        queue=COMPLETED_DELIVERY_QUEUE_NAME, on_message_callback=callback_completed_delivery, auto_ack=True
    )
    print("Log: Reading a message from a queue completed_delivery_queue_savitskiy", flush=True)
    channel.start_consuming()