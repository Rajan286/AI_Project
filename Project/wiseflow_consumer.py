import pika
import json
import os

def callback(ch, method, properties, body):
    try:
        student = json.loads(body)
        name = student["name"]
        sid = student["id"]
        programs = student["study_programs"]
        credits = student["credits"]

        entry = {
            "name": name,
            "id": sid,
            "study_programs": programs,
            "credits": credits
        }

        filename = "wyseflow_data.json"
        if os.path.exists(filename):
            with open(filename, "r") as f:
                data = json.load(f)
        else:
            data = []

        if not any(s["id"] == sid for s in data):
            data.append(entry)
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)

        print(f"[x] Student {name} processed for WyseFlow")

    except Exception as e:
        print(f"[!] Failed to process message: {e}")

def start_consumer():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='wiseflow_queue')
        channel.basic_consume(queue='wiseflow_queue', on_message_callback=callback, auto_ack=True)
        print("[*] Waiting for messages in WyseFlow...")
        channel.start_consuming()
    except Exception as e:
        print(f"[!] WyseFlow connection error: {e}")

class WyseFlowReceiver:
    def start(self):
        start_consumer()

if __name__ == '__main__':
    start_consumer()
