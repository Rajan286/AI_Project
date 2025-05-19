import pika
import json

def callback(ch, method, properties, body):
    student = json.loads(body)
    print(f"[WyseFlow] Received data: {student['id']} - Credits: {student['credits']}")

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='wyseflow_queue', durable=True)
channel.basic_consume(queue='wyseflow_queue', on_message_callback=callback, auto_ack=True)

print('[WyseFlow] Waiting for messages...')
channel.start_consuming()
