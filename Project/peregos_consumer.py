import pika
import json
import os

def callback(ch, method, properties, body):
    try:
        student = json.loads(body)
        name = student.get("name")
        student_id = student.get("id")
        study_programs = student.get("study_programs")

        if not name or not student_id or not study_programs:
            print(f"[!] Incomplete student data received, skipping.")
            return

        entry = {
            "name": name,
            "id": student_id,
            "study_programs": study_programs
        }

        filename = "peregos_data.json"
        if os.path.exists(filename):
            with open(filename, "r") as f:
                data = json.load(f)
        else:
            data = []

        if any(s["id"] == student_id for s in data):
            print(f"[!] Duplicate student ID ignored in Peregos: {student_id}")
            return

        data.append(entry)

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        print(f"[x] Student {name} processed for Peregos")

    except Exception as e:
        print(f"[!] Error processing message in Peregos: {e}")

def start_consumer():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='peregos_queue')
        channel.basic_consume(queue='peregos_queue', on_message_callback=callback, auto_ack=True)
        print("[*] Waiting for messages in Peregos...")
        channel.start_consuming()
    except Exception as e:
        print(f"[!] Peregos connection error: {e}")

class PeregosReceiver:
    def start(self):
        start_consumer()

if __name__ == '__main__':
    start_consumer()
