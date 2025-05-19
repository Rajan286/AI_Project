import pika
import json

def callback(ch, method, properties, body):
    student = json.loads(body)
    print(f"[Peregos] Received data: {student['id']} - {student['name']} - {student['programs']}")

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='peregos_queue', durable=True)
channel.basic_consume(queue='peregos_queue', on_message_callback=callback, auto_ack=True)

print('[Peregos] Waiting for messages...')
channel.start_consuming()
