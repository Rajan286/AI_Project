import pika

def setup_queues():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Queues für Peregos und WyseFlow
    channel.queue_declare(queue='peregos_queue', durable=True)
    channel.queue_declare(queue='wyseflow_queue', durable=True)

    connection.close()

if __name__ == "__main__":
    setup_queues()
