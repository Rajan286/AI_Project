import tkinter as tk
from tkinter import messagebox
import pika
import json
import os

STORAGE_FILE = 'students.json'

# Hardcodierter Student (immer mitsenden)
DEFAULT_STUDENT = {
    "id": "000000",
    "name": "Systemtester",
    "programs": ["Systemprüfung"],
    "credits": {"Systemprüfung": 100}
}

# Lade bestehende Studenten aus Datei
def load_students():
    if not os.path.exists(STORAGE_FILE):
        return []
    with open(STORAGE_FILE, 'r') as f:
        return json.load(f)

# Speichere neue Studentenliste in Datei
def save_students(students):
    with open(STORAGE_FILE, 'w') as f:
        json.dump(students, f, indent=2)

def send_all_students(new_student):
    students = load_students()
    students.append(new_student)
    save_students(students)

    # Füge den hardcodierten Student hinzu
    full_list = [DEFAULT_STUDENT] + students

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        for student in full_list:
            message = json.dumps(student)
            channel.basic_publish(exchange='', routing_key='peregos_queue', body=message)
            channel.basic_publish(exchange='', routing_key='wyseflow_queue', body=message)

        connection.close()
        messagebox.showinfo("Erfolg", f"{len(full_list)} Studenten erfolgreich gesendet!")
    except Exception as e:
        messagebox.showerror("Verbindungsfehler", str(e))

def on_send():
    student_id = entry_id.get().strip()
    name = entry_name.get().strip()
    programs = [p.strip() for p in entry_programs.get().split(',') if p.strip()]
    credits_input = [c.strip() for c in entry_credits.get().split(',') if c.strip()]

    if not (student_id and name and programs and credits_input):
        messagebox.showerror("Fehler", "Bitte alle Felder korrekt ausfüllen!")
        return

    if len(programs) != len(credits_input):
        messagebox.showerror("Fehler", "Programme und Credits müssen gleich viele Einträge haben.")
        return

    try:
        credits = {programs[i]: int(credits_input[i]) for i in range(len(programs))}
    except ValueError:
        messagebox.showerror("Fehler", "Credits müssen ganze Zahlen sein.")
        return

    student = {
        "id": student_id,
        "name": name,
        "programs": programs,
        "credits": credits
    }

    send_all_students(student)
    # Felder leeren nach erfolgreichem Senden
    entry_id.delete(0, tk.END)
    entry_name.delete(0, tk.END)
    entry_programs.delete(0, tk.END)
    entry_credits.delete(0, tk.END)

# GUI Aufbau
root = tk.Tk()
root.title("HIS Producer GUI")

tk.Label(root, text="Student ID").grid(row=0, column=0, sticky='e')
entry_id = tk.Entry(root)
entry_id.grid(row=0, column=1)

tk.Label(root, text="Name").grid(row=1, column=0, sticky='e')
entry_name = tk.Entry(root)
entry_name.grid(row=1, column=1)

tk.Label(root, text="Studiengänge (mit Komma)").grid(row=2, column=0, sticky='e')
entry_programs = tk.Entry(root)
entry_programs.grid(row=2, column=1)

tk.Label(root, text="Credits (mit Komma)").grid(row=3, column=0, sticky='e')
entry_credits = tk.Entry(root)
entry_credits.grid(row=3, column=1)

tk.Button(root, text="Senden", command=on_send).grid(row=4, column=0, columnspan=2, pady=10)

root.mainloop()
