import pika
import json

def send_student_data(student):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    message = json.dumps(student)

    # Nachrichten an beide Queues schicken
    channel.basic_publish(exchange='', routing_key='peregos_queue', body=message)
    channel.basic_publish(exchange='', routing_key='wyseflow_queue', body=message)

    print(f"Sent student data: {student['id']}")

    connection.close()

if __name__ == "__main__":
    student_data = {
        "id": "123456",
        "name": "Parmdip",
        "programs": ["Informatik", "Wirtschaft"],
        "credits": {
            "Informatik": 120,
            "Wirtschaft": 60
        }
    }
    send_student_data(student_data)
