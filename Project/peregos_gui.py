import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
import pika

class PeregosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Peregos Receiver")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(expand=True, fill="both")

        self.status_label = tk.Label(frame, text="Status: Not running", font=("Arial", 12))
        self.status_label.pack(pady=5)

        self.latest_label = tk.Label(frame, text="Latest Student: ---", font=("Arial", 11), wraplength=450, justify="left")
        self.latest_label.pack(pady=10)

        self.start_button = tk.Button(frame, text="Start Listening", font=("Arial", 11), command=self.start_receiver)
        self.start_button.pack(pady=5)

        self.view_students_button = tk.Button(frame, text="View All Students", font=("Arial", 11), command=self.show_students)
        self.view_students_button.pack(pady=5)

    def start_receiver(self):
        self.status_label.config(text="Status: Listening for messages...")
        self.start_button.config(state=tk.DISABLED)
        threading.Thread(target=self.run_receiver, daemon=True).start()

    def run_receiver(self):
        def callback(ch, method, properties, body):
            try:
                student = json.loads(body)
                name = student.get("name")
                student_id = student.get("id")
                programs = student.get("study_programs")

                if not name or not student_id or not programs:
                    self.update_latest("[Invalid message received]")
                    return

                entry = {
                    "name": name,
                    "id": student_id,
                    "study_programs": programs
                }

                # Update JSON file
                filename = "peregos_data.json"
                if os.path.exists(filename):
                    with open(filename, "r") as f:
                        data = json.load(f)
                else:
                    data = []

                if not any(s["id"] == student_id for s in data):
                    data.append(entry)
                    with open(filename, "w") as f:
                        json.dump(data, f, indent=2)

                # Update GUI
                self.update_latest(f"{name} (ID: {student_id}) - {', '.join(programs)}")

            except Exception as e:
                self.update_latest(f"[Error] {e}")

        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='peregos_queue', durable=True)
            channel.basic_consume(queue='peregos_queue', on_message_callback=callback, auto_ack=True)
            channel.start_consuming()
        except Exception as e:
            self.update_latest(f"[Connection Error] {e}")
            self.status_label.config(text="Status: Error")
            self.start_button.config(state=tk.NORMAL)

    def update_latest(self, text):
        self.latest_label.config(text=f"Latest Student: {text}")

    def show_students(self):
        popup = tk.Toplevel(self.root)
        popup.title("All Peregos Students")
        popup.geometry("500x300")

        if os.path.exists("peregos_data.json"):
            with open("peregos_data.json", "r") as f:
                students = json.load(f)
        else:
            students = []

        text = tk.Text(popup, wrap='word')
        text.pack(expand=True, fill='both')
        for s in students:
            info = f"Name: {s['name']}, ID: {s['id']}, Programs: {', '.join(s['study_programs'])}\n"
            text.insert(tk.END, info)
        text.config(state='disabled')

if __name__ == '__main__':
    root = tk.Tk()
    app = PeregosGUI(root)
    root.mainloop()
