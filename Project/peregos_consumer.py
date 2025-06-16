import pika
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

PEREGOS_FILE = "peregos_data.json"
PROCESSED_IDS_FILE = "peregos_processed_ids.json"
QUEUE_NAME = "peregos"
RABBITMQ_HOST = "127.0.0.1"  # explizit IPv4

def load_existing_ids():
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    with open(PROCESSED_IDS_FILE, 'r') as f:
        return set(json.load(f))

def save_processed_id(student_id, processed_ids):
    processed_ids.add(student_id)
    with open(PROCESSED_IDS_FILE, 'w') as f:
        json.dump(list(processed_ids), f)

def store_student_data(student):
    if not os.path.exists(PEREGOS_FILE):
        data = []
    else:
        with open(PEREGOS_FILE, 'r') as f:
            data = json.load(f)

    new_entry = {
        "name": student["name"],
        "id": student["id"],
        "study_programs": student["study_programs"]
    }

    data.append(new_entry)
    with open(PEREGOS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    logging.info(f"Student gespeichert: {student['id']}")

def callback(ch, method, properties, body):
    try:
        student = json.loads(body.decode())

        if student["id"] in processed_ids:
            logging.warning(f"Duplikat ignoriert: {student['id']}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        store_student_data(student)
        save_processed_id(student["id"], processed_ids)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logging.error(f"Fehler beim Verarbeiten der Nachricht: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    global processed_ids
    processed_ids = load_existing_ids()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    logging.info("Peregos Consumer gestartet...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
