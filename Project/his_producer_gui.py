import tkinter as tk
import json
import pika
import os

STUDENT_FILE = "students.json"

class HISStudentRegistrationGUI:
    def __init__(self, master):
        self.master = master
        master.title("Register Student (HIS)")

        tk.Label(master, text="Full Name:").pack()
        self.entry_name = tk.Entry(master)
        self.entry_name.pack()

        tk.Label(master, text="Student ID:").pack()
        self.entry_id = tk.Entry(master)
        self.entry_id.pack()

        tk.Label(master, text="Study Programs (comma separated):").pack()
        self.entry_programs = tk.Entry(master)
        self.entry_programs.pack()

        tk.Label(master, text="Credits per Program (comma separated):").pack()
        self.entry_credits = tk.Entry(master)
        self.entry_credits.pack()

        tk.Button(master, text="Register Student", command=self.register_student).pack(pady=5)
        tk.Button(master, text="Show All Students", command=self.show_all_students).pack(pady=5)

        self.output = tk.Text(master, height=10, width=55)
        self.output.pack(pady=10)

    def register_student(self):
        name = self.entry_name.get().strip()
        student_id = self.entry_id.get().strip()
        programs = [s.strip() for s in self.entry_programs.get().split(",") if s.strip()]
        credits_raw = self.entry_credits.get().split(",")
        credits = []

        for c in credits_raw:
            c = c.strip()
            if c.isdigit():
                credits.append(int(c))
            else:
                self.output.insert(tk.END, f"⚠️ Invalid credit: '{c}'\n")
                return

        if not name or not student_id or len(programs) != len(credits):
            self.output.insert(tk.END, "⚠️ Check fields: Name, ID, and program/credit count match.\n")
            return

        student = {
            "name": name,
            "id": student_id,
            "study_programs": programs,
            "credits": credits
        }

        self.save_student(student)
        self.send_to_systems(student)

        self.output.insert(tk.END, f"✅ Registered and sent: {name} ({student_id})\n")

        self.entry_name.delete(0, tk.END)
        self.entry_id.delete(0, tk.END)
        self.entry_programs.delete(0, tk.END)
        self.entry_credits.delete(0, tk.END)

    def send_to_systems(self, student):
        if not student["study_programs"] or not student["credits"]:
            msg = "⚠️ No study program or credits provided – nothing sent.\n"
            self.output.insert(tk.END, msg)
            print(msg)
            return

        try:
            peregos_data = {
                "name": student["name"],
                "id": student["id"],
                "study_programs": student["study_programs"]
            }

            wyseflow_data = {
                "name": student["name"],
                "id": student["id"],
                "study_programs": student["study_programs"],
                "credits": student["credits"]
            }

            print("→ Sent to Peregos:", peregos_data)
            print("→ Sent to WyseFlow:", wyseflow_data)

            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='peregos_queue', durable=True)
            channel.queue_declare(queue='wyseflow_queue', durable=True)

            channel.basic_publish(exchange='', routing_key='peregos_queue', body=json.dumps(peregos_data))
            channel.basic_publish(exchange='', routing_key='wyseflow_queue', body=json.dumps(wyseflow_data))
            connection.close()

        except Exception as e:
            error_msg = f"⚠️ Error while sending: {e}\n"
            self.output.insert(tk.END, error_msg)
            print(error_msg)

    def save_student(self, student):
        students = []
        if os.path.exists(STUDENT_FILE):
            try:
                with open(STUDENT_FILE, "r") as f:
                    students = json.load(f)
            except json.JSONDecodeError:
                pass

        students.append(student)
        with open(STUDENT_FILE, "w") as f:
            json.dump(students, f, indent=2)

    def show_all_students(self):
        self.output.delete("1.0", tk.END)
        if os.path.exists(STUDENT_FILE):
            try:
                with open(STUDENT_FILE, "r") as f:
                    students = json.load(f)
                    for s in students:
                        self.output.insert(tk.END, f"{s['name']} ({s['id']}): {s['study_programs']} – {s['credits']}\n")
            except Exception as e:
                self.output.insert(tk.END, f"⚠️ Could not load students: {e}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = HISStudentRegistrationGUI(root)
    root.mainloop()
