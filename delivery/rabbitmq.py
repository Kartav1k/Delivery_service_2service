import json
import pika

RABBITMQ_HOST="51.250.26.59"
RABBITMQ_PORT=5672
RABBITMQ_USER='guest'
RABBITMQ_PASSWORD='guest123'
DELIVERY_QUEUE_NAME = "start_delivery_queue_savitskiy"

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