import tkinter as tk
import json
import os
import threading
import time
import pika
from tkinter import scrolledtext, messagebox
from his_producer import (
    load_students,
    load_programs,
    validate_student,
    connect_to_rabbitmq,
    send_to_rabbitmq,
    buffer_message
)

BUFFER_FILE = "buffered_data.json"
STUDENT_FILE = "students.json"
PROGRAMS_FILE = "programs.json"
RABBITMQ_HOST = "127.0.0.1"

class ProducerGUI:
    def __init__(self, master):
        self.master = master
        master.title("HIS Producer Monitor")

        self.connection_label = tk.Label(master, text="RabbitMQ Status: UNKNOWN", bg="gray", fg="white", width=40)
        self.connection_label.pack(pady=5)

        self.status_label = tk.Label(master, text="Last Status: -", width=40)
        self.status_label.pack(pady=5)

        self.buffer_label = tk.Label(master, text="Buffered Messages: 0", width=40)
        self.buffer_label.pack(pady=5)

        self.student_label = tk.Label(master, text="Current Student: -", width=40)
        self.student_label.pack(pady=5)

        self.view_students_button = tk.Button(master, text="View All Students", command=self.show_students)
        self.view_students_button.pack(pady=2)

        self.view_programs_button = tk.Button(master, text="View Study Programs", command=self.show_programs)
        self.view_programs_button.pack(pady=2)

        self.view_buffer_button = tk.Button(master, text="View Buffered Messages", command=self.show_buffered)
        self.view_buffer_button.pack(pady=2)

        self.add_student_button = tk.Button(master, text="Add Student", command=self.open_add_student_popup)
        self.add_student_button.pack(pady=2)

        self.manage_programs_button = tk.Button(master, text="Manage Study Programs", command=self.open_manage_programs_popup)
        self.manage_programs_button.pack(pady=2)

        self.check_rabbitmq_button = tk.Button(master, text="Check RabbitMQ Status", command=self.manual_check_connection)
        self.check_rabbitmq_button.pack(pady=2)

        self.output_text = scrolledtext.ScrolledText(master, width=70, height=20)
        self.output_text.pack(pady=10)

        self.running = False
        self.update_connection_status(self.check_connection())
        self.update_buffer_count()

        self.start_buffer_watcher()
    def check_connection(self):
        try:
            conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            conn.close()
            return True
        except:
            return False

    def manual_check_connection(self):
        connected = self.check_connection()
        self.update_connection_status(connected)
        msg = "CONNECTED" if connected else "NOT AVAILABLE"
        self.update_status(f"Manual check: RabbitMQ {msg}")

    def update_connection_status(self, connected):
        if connected:
            self.connection_label.config(text="RabbitMQ Status: CONNECTED", bg="green")
        else:
            self.connection_label.config(text="RabbitMQ Status: NOT AVAILABLE", bg="red")

    def update_status(self, msg):
        self.status_label.config(text=f"Last Status: {msg}")

    def update_buffer_count(self):
        if os.path.exists(BUFFER_FILE):
            with open(BUFFER_FILE, 'r') as f:
                lines = f.readlines()
            self.buffer_label.config(text=f"Buffered Messages: {len(lines)}")
        else:
            self.buffer_label.config(text="Buffered Messages: 0")

    def update_student_info(self, student):
        self.student_label.config(text=f"Current Student: {student['name']} ({student['id']})")

    def show_students(self):
        try:
            with open(STUDENT_FILE, 'r') as f:
                students = json.load(f)
            output = "\n".join([f"{s['id']} – {s['name']}" for s in students])
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, f"📚 Students:\n{output}")
        except Exception as e:
            self.output_text.insert(tk.END, f"\nError loading students: {e}")

    def show_programs(self):
        try:
            with open(PROGRAMS_FILE, 'r') as f:
                programs = json.load(f)
            output = "\n".join([f"{name}: {info['max_credits']} CP, Start: {info['start_semester']}" for name, info in programs.items()])
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, f"🎓 Study Programs:\n{output}")
        except Exception as e:
            self.output_text.insert(tk.END, f"\nError loading programs: {e}")

    def show_buffered(self):
        if not os.path.exists(BUFFER_FILE):
            self.output_text.insert(tk.END, "\n📦 No buffered messages.")
            return
        try:
            with open(BUFFER_FILE, 'r') as f:
                lines = f.readlines()
            entries = [json.loads(line.strip()) for line in lines]
            output = "\n".join([f"{s['id']} – {s['name']}" for s in entries])
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, f"📦 Buffered Students:\n{output}")
        except Exception as e:
            self.output_text.insert(tk.END, f"\nError reading buffer file: {e}")
    def open_add_student_popup(self):
        popup = tk.Toplevel(self.master)
        popup.title("Add New Student")

        tk.Label(popup, text="Name:").grid(row=0, column=0)
        name_entry = tk.Entry(popup, width=40)
        name_entry.grid(row=0, column=1)

        tk.Label(popup, text="ID:").grid(row=1, column=0)
        id_entry = tk.Entry(popup, width=40)
        id_entry.grid(row=1, column=1)

        tk.Label(popup, text="Study Programs (comma-separated):").grid(row=2, column=0)
        programs_entry = tk.Entry(popup, width=40)
        programs_entry.grid(row=2, column=1)

        tk.Label(popup, text="Credits (comma-separated):").grid(row=3, column=0)
        credits_entry = tk.Entry(popup, width=40)
        credits_entry.grid(row=3, column=1)

        def save_student():
            name = name_entry.get().strip()
            student_id = id_entry.get().strip()
            programs = [p.strip() for p in programs_entry.get().split(',')]
            credits = credits_entry.get().split(',')

            if not name or not student_id or not programs or not credits:
                messagebox.showerror("Input Error", "All fields are required.")
                return

            try:
                credits = [int(c.strip()) for c in credits]
            except ValueError:
                messagebox.showerror("Input Error", "Credits must be numbers.")
                return

            if len(programs) != len(credits):
                messagebox.showerror("Input Error", "Programs and Credits count must match.")
                return

            with open(PROGRAMS_FILE, 'r') as f:
                valid_programs = json.load(f)

            if not all(p in valid_programs for p in programs):
                messagebox.showerror("Validation Error", "One or more study programs are invalid.")
                return

            student = {
                "name": name,
                "id": student_id,
                "study_programs": programs,
                "credits": credits
            }

            try:
                students = load_students()
                for s in students:
                    if s['id'] == student_id:
                        messagebox.showerror("Duplicate ID", f"Student ID {student_id} already exists.")
                        return
                students.append(student)
                with open(STUDENT_FILE, 'w') as f:
                    json.dump(students, f, indent=2)
            except Exception as e:
                messagebox.showerror("File Error", f"Could not save student: {e}")
                return

            connection, channel = connect_to_rabbitmq()
            if channel:
                if send_to_rabbitmq(channel, student):
                    self.update_status("Student sent.")
                else:
                    buffer_message(student)
                    self.update_status("Send failed – buffered.")
                connection.close()
            else:
                buffer_message(student)
                self.update_status("RabbitMQ not reachable – buffered.")

            self.update_student_info(student)
            self.update_buffer_count()
            popup.destroy()
            self.show_students()

        tk.Button(popup, text="Save Student", command=save_student).grid(row=4, columnspan=2, pady=10)
    def open_manage_programs_popup(self):
        popup = tk.Toplevel(self.master)
        popup.title("Manage Study Programs")

        tk.Label(popup, text="Program Name:").grid(row=0, column=0)
        name_entry = tk.Entry(popup, width=40)
        name_entry.grid(row=0, column=1)

        tk.Label(popup, text="Max Credits:").grid(row=1, column=0)
        credits_entry = tk.Entry(popup, width=40)
        credits_entry.grid(row=1, column=1)

        tk.Label(popup, text="Start Semester (WS/SS):").grid(row=2, column=0)
        start_entry = tk.Entry(popup, width=40)
        start_entry.grid(row=2, column=1)

        def add_program():
            name = name_entry.get().strip()
            max_credits = credits_entry.get().strip()
            start = start_entry.get().strip().upper()

            if not name or not max_credits or not start:
                messagebox.showerror("Input Error", "All fields are required.")
                return
            if start not in ['WS', 'SS']:
                messagebox.showerror("Input Error", "Start must be WS or SS.")
                return
            try:
                max_credits = int(max_credits)
            except ValueError:
                messagebox.showerror("Input Error", "Credits must be a number.")
                return

            with open(PROGRAMS_FILE, 'r') as f:
                programs = json.load(f)

            if name in programs:
                messagebox.showerror("Duplicate", "Program already exists.")
                return

            programs[name] = {"max_credits": max_credits, "start_semester": start}
            with open(PROGRAMS_FILE, 'w') as f:
                json.dump(programs, f, indent=2)
            messagebox.showinfo("Success", f"Program '{name}' added.")
            name_entry.delete(0, tk.END)
            credits_entry.delete(0, tk.END)
            start_entry.delete(0, tk.END)
            refresh_dropdown()

        tk.Button(popup, text="Add Program", command=add_program).grid(row=3, columnspan=2, pady=10)

        tk.Label(popup, text="Delete Existing Program:").grid(row=4, column=0)
        program_var = tk.StringVar()
        program_dropdown = tk.OptionMenu(popup, program_var, "")
        program_dropdown.grid(row=4, column=1)

        def refresh_dropdown():
            program_dropdown['menu'].delete(0, 'end')
            with open(PROGRAMS_FILE, 'r') as f:
                programs = json.load(f)
            for name in programs:
                program_dropdown['menu'].add_command(label=name, command=tk._setit(program_var, name))

        def delete_program():
            selected = program_var.get()
            if not selected:
                messagebox.showerror("Input Error", "No program selected.")
                return
            with open(PROGRAMS_FILE, 'r') as f:
                programs = json.load(f)
            if selected not in programs:
                messagebox.showerror("Error", "Program not found.")
                return
            del programs[selected]
            with open(PROGRAMS_FILE, 'w') as f:
                json.dump(programs, f, indent=2)
            messagebox.showinfo("Deleted", f"Program '{selected}' removed.")
            refresh_dropdown()

        tk.Button(popup, text="Delete Program", command=delete_program).grid(row=5, columnspan=2, pady=10)
        refresh_dropdown()

    def process_buffered_messages(self):
        if not os.path.exists(BUFFER_FILE):
            return
        if not self.check_connection():
            return
        with open(BUFFER_FILE, 'r') as f:
            lines = f.readlines()
        remaining = []
        for line in lines:
            try:
                student = json.loads(line.strip())
                connection, channel = connect_to_rabbitmq()
                if channel:
                    if send_to_rabbitmq(channel, student):
                        self.update_status(f"Buffered student sent: {student['id']}")
                        self.update_student_info(student)
                    else:
                        remaining.append(line)
                    connection.close()
                else:
                    remaining.append(line)
            except Exception:
                remaining.append(line)
        with open(BUFFER_FILE, 'w') as f:
            for entry in remaining:
                f.write(entry)
        self.update_buffer_count()

    def start_buffer_watcher(self):
        def watcher():
            while True:
                self.process_buffered_messages()
                time.sleep(10)
        thread = threading.Thread(target=watcher, daemon=True)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    gui = ProducerGUI(root)
    root.mainloop()
