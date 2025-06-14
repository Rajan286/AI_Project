import pika
import json
import threading
import os

DATA_FILE = "peregos_data.json"

class PeregosReceiver:
    def __init__(self, callback):
        self.callback = callback

    def start_listening(self):
        def run():
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='peregos_queue', durable=True)

            def on_message(ch, method, properties, body):
                data = json.loads(body)
                print("[Peregos] Nachricht empfangen")
                self.save_to_file(data)
                self.callback(data)

            channel.basic_consume(queue='peregos_queue', on_message_callback=on_message, auto_ack=True)
            print("[Peregos] Lauscht auf Nachrichten...")
            channel.start_consuming()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def save_to_file(self, data):
        all_data = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    all_data = json.load(f)
            except json.JSONDecodeError:
                pass

        all_data.append(data)
        with open(DATA_FILE, "w") as f:
            json.dump(all_data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
