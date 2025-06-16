import pika
import json
import time
import os
import threading
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Datei-Pfade
STUDENT_FILE = "students.json"
PROGRAMS_FILE = "programs.json"
BUFFER_FILE = "buffered_data.json"

# Globale Queue-Konfiguration
QUEUE_NAMES = ["peregos", "wyseflow"]
RABBITMQ_HOST = 'localhost'


def load_students():
    with open(STUDENT_FILE, 'r') as f:
        return json.load(f)


def load_programs():
    with open(PROGRAMS_FILE, 'r') as f:
        return json.load(f)


def validate_student(student, valid_programs):
    for program in student["study_programs"]:
        if program not in valid_programs:
            logging.warning(f"Ungültiger Studiengang '{program}' für Student {student['id']}")
            return False
    return True


def connect_to_rabbitmq():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
        channel = connection.channel()
        for queue in QUEUE_NAMES:
            channel.queue_declare(queue=queue, durable=True)
        return connection, channel
    except pika.exceptions.AMQPConnectionError:
        logging.error("RabbitMQ nicht erreichbar.")
        return None, None


def send_to_rabbitmq(channel, student):
    message = json.dumps(student)
    for queue in QUEUE_NAMES:
        try:
            channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)  # persistent
            )
            logging.info(f"Nachricht an Queue '{queue}' gesendet: {student['id']}")
        except Exception as e:
            logging.error(f"Fehler beim Senden an Queue '{queue}': {e}")
            return False
    return True


def buffer_message(student):
    with open(BUFFER_FILE, 'a') as f:
        f.write(json.dumps(student) + "\n")
    logging.info(f"Student {student['id']} wurde zwischengespeichert.")


def retry_buffered_messages():
    while True:
        if not os.path.exists(BUFFER_FILE):
            time.sleep(15)
            continue

        try:
            connection, channel = connect_to_rabbitmq()
            if not channel:
                time.sleep(15)
                continue

            with open(BUFFER_FILE, 'r') as f:
                lines = f.readlines()

            success_lines = []
            for line in lines:
                student = json.loads(line.strip())
                if send_to_rabbitmq(channel, student):
                    success_lines.append(line)

            # Nur nicht erfolgreich gesendete Zeilen beibehalten
            with open(BUFFER_FILE, 'w') as f:
                for line in lines:
                    if line not in success_lines:
                        f.write(line)

            connection.close()

        except Exception as e:
            logging.error(f"Fehler beim Wiederholen gepufferter Nachrichten: {e}")

        time.sleep(15)  # Intervall für Retry


def main():
    students = load_students()
    valid_programs = load_programs()

    # Starte Retry-Thread
    retry_thread = threading.Thread(target=retry_buffered_messages, daemon=True)
    retry_thread.start()

    for student in students:
        if not validate_student(student, valid_programs):
            continue

        connection, channel = connect_to_rabbitmq()
        if channel:
            if not send_to_rabbitmq(channel, student):
                buffer_message(student)
            connection.close()
        else:
            buffer_message(student)

        time.sleep(1)  # optional: um RabbitMQ nicht zu fluten


if __name__ == "__main__":
    main()
