import pika

def setup_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Queues mit durability deklarieren
    channel.queue_declare(queue='peregos_queue', durable=True)
    channel.queue_declare(queue='wyseflow_queue', durable=True)

    print("RabbitMQ-Setup abgeschlossen: Queues mit durable=True erstellt.")
    connection.close()

if __name__ == "__main__":
    setup_rabbitmq()
