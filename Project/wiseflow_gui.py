import tkinter as tk
import json
import os
import pika
import threading
from tkinter import scrolledtext, messagebox

WISEFLOW_FILE = "wyseflow_data.json"
PROCESSED_IDS_FILE = "wyseflow_processed_ids.json"
QUEUE_NAME = "wyseflow"
RABBITMQ_HOST = "127.0.0.1"

class WiseFlowGUI:
    def __init__(self, master):
        self.master = master
        master.title("WiseFlow Consumer")

        self.connection_label = tk.Label(master, text="RabbitMQ: UNKNOWN", bg="gray", fg="white", width=40)
        self.connection_label.pack(pady=5)

        self.status_label = tk.Label(master, text="Status: -", width=40)
        self.status_label.pack(pady=5)

        self.student_label = tk.Label(master, text="Last Student: -", width=40)
        self.student_label.pack(pady=5)

        self.start_button = tk.Button(master, text="Start Listening", command=self.start_consuming)
        self.start_button.pack(pady=5)

        self.view_all_button = tk.Button(master, text="View All Students", command=self.show_all_students)
        self.view_all_button.pack(pady=2)

        self.output_text = scrolledtext.ScrolledText(master, width=60, height=15)
        self.output_text.pack(pady=5)

        self.processed_ids = self.load_existing_ids()
        self.update_connection_status(self.check_connection())

    def check_connection(self):
        try:
            conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            conn.close()
            return True
        except:
            return False

    def update_connection_status(self, ok):
        if ok:
            self.connection_label.config(text="RabbitMQ: CONNECTED", bg="green")
        else:
            self.connection_label.config(text="RabbitMQ: NOT AVAILABLE", bg="red")

    def load_existing_ids(self):
        if not os.path.exists(PROCESSED_IDS_FILE):
            return set()
        with open(PROCESSED_IDS_FILE, 'r') as f:
            return set(json.load(f))

    def save_processed_id(self, student_id):
        self.processed_ids.add(student_id)
        with open(PROCESSED_IDS_FILE, 'w') as f:
            json.dump(list(self.processed_ids), f)

    def store_student_data(self, student):
        if not os.path.exists(WISEFLOW_FILE):
            data = []
        else:
            with open(WISEFLOW_FILE, 'r') as f:
                data = json.load(f)

        entry = {
            "name": student["name"],
            "id": student["id"],
            "study_programs": student["study_programs"],
            "credits": student["credits"]
        }

        data.append(entry)
        with open(WISEFLOW_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def show_all_students(self):
        if not os.path.exists(WISEFLOW_FILE):
            self.output_text.insert(tk.END, "No data found.\n")
            return
        with open(WISEFLOW_FILE, 'r') as f:
            data = json.load(f)
        self.output_text.delete("1.0", tk.END)
        for entry in data:
            programs = ", ".join(entry["study_programs"])
            credits = ", ".join(map(str, entry["credits"]))
            self.output_text.insert(tk.END, f"{entry['id']} – {entry['name']} – {programs} – {credits} CP\n")

    def callback(self, ch, method, properties, body):
        try:
            student = json.loads(body.decode())

            if student["id"] in self.processed_ids:
                self.status_label.config(text=f"Duplicate skipped: {student['id']}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            self.student_label.config(text=f"Last Student: {student['name']} ({student['id']})")
            self.status_label.config(text="Student received")
            self.store_student_data(student)
            self.save_processed_id(student["id"])
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self.status_label.config(text=f"Error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def consume(self):
        try:
            conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = conn.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=1)
            self.update_connection_status(True)
        except Exception as e:
            self.update_connection_status(False)
            self.status_label.config(text=f"Connection Error: {e}")
            return

        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=self.callback)
        channel.start_consuming()

    def start_consuming(self):
        thread = threading.Thread(target=self.consume, daemon=True)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    gui = WiseFlowGUI(root)
    root.mainloop()
