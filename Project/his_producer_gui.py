import tkinter as tk
from tkinter import messagebox, ttk
import json
import pika
import os
from program_manager import validate_student_credits, find_unknown_programs, add_program, load_programs, save_programs

class HISProducerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HIS Producer")
        self.root.geometry("500x550")

        tk.Label(root, text="Name:").pack()
        self.name_entry = tk.Entry(root)
        self.name_entry.pack()

        tk.Label(root, text="Student ID:").pack()
        self.id_entry = tk.Entry(root)
        self.id_entry.pack()

        tk.Label(root, text="Study Programs (comma separated):").pack()
        self.study_entry = tk.Entry(root)
        self.study_entry.pack()

        tk.Label(root, text="Credits (comma separated):").pack()
        self.credits_entry = tk.Entry(root)
        self.credits_entry.pack()

        tk.Button(root, text="Send", command=self.send_data).pack(pady=5)
        tk.Button(root, text="Manage Study Programs (View, Add, Delete)", command=self.manage_programs).pack(pady=5)
        tk.Button(root, text="View All Students", command=self.show_all_students).pack(pady=5)

    def send_data(self):
        name = self.name_entry.get().strip()
        student_id = self.id_entry.get().strip()
        study_programs = [s.strip() for s in self.study_entry.get().split(',')]
        credits_str = self.credits_entry.get().strip()

        if not name or not student_id or not study_programs or not credits_str:
            messagebox.showerror("Error", "All fields must be filled.")
            return

        try:
            credits = list(map(int, credits_str.split(',')))
        except ValueError:
            messagebox.showerror("Error", "Credits must be integers.")
            return

        if len(study_programs) != len(credits):
            messagebox.showerror("Error", "Number of programs and credits must match.")
            return

        if os.path.exists("students.json"):
            with open("students.json", "r") as f:
                existing_students = json.load(f)
        else:
            existing_students = []

        if any(s["id"] == student_id for s in existing_students):
            messagebox.showerror("Duplicate ID", f"A student with ID {student_id} is already registered.")
            return

        unknown_programs = find_unknown_programs(study_programs)
        if unknown_programs:
            messagebox.showerror(
                "Unknown Programs",
                f"The following programs are not registered:\n{', '.join(unknown_programs)}\n\nPlease add them via 'Manage Study Programs'."
            )
            return

        invalid = validate_student_credits(study_programs, credits)
        if invalid:
            msg = "\n".join([f"{prog}: {cp} > {max_cp}" for prog, cp, max_cp in invalid])
            messagebox.showerror("Invalid Credits", f"Too many credits:\n{msg}")
            return

        student = {
            "name": name,
            "id": student_id,
            "study_programs": study_programs,
            "credits": credits
        }

        existing_students.append(student)
        with open("students.json", "w") as f:
            json.dump(existing_students, f, indent=2)

        # Send to RabbitMQ (now with durable queues)
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='peregos_queue', durable=True)
            channel.queue_declare(queue='wiseflow_queue', durable=True)
            body = json.dumps(student)
            channel.basic_publish(exchange='', routing_key='peregos_queue', body=body)
            channel.basic_publish(exchange='', routing_key='wiseflow_queue', body=body)
            connection.close()
            messagebox.showinfo("Success", "Student data sent successfully.")
            self.clear_fields()
        except pika.exceptions.AMQPConnectionError as e:
            messagebox.showerror("Connection Error", f"Failed to connect to RabbitMQ:\n{e}")

    def manage_programs(self):
        popup = tk.Toplevel(self.root)
        popup.title("Manage Study Programs")
        popup.geometry("600x450")

        programs = load_programs()
        program_frame = tk.Frame(popup)
        program_frame.pack(pady=10, fill='x')

        def refresh_list():
            for widget in program_frame.winfo_children():
                widget.destroy()
            for name, info in programs.items():
                row = tk.Frame(program_frame)
                row.pack(fill='x', padx=10, pady=2)
                label = tk.Label(row, text=f"{name}: {info['max_credits']} CP, Start: {info['start_semester']}", anchor='w')
                label.pack(side='left', fill='x', expand=True)
                btn = tk.Button(row, text="Delete", command=lambda n=name: delete_program(n))
                btn.pack(side='right')

        def delete_program(name):
            if messagebox.askyesno("Delete Program", f"Are you sure you want to delete '{name}'?"):
                programs.pop(name, None)
                save_programs(programs)
                refresh_list()

        refresh_list()

        separator = tk.Label(popup, text="Add New Study Program", font=('Arial', 10, 'bold'))
        separator.pack(pady=(10, 0))

        form_frame = tk.Frame(popup)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Program Name:").grid(row=0, column=0, sticky='e')
        name_entry = tk.Entry(form_frame)
        name_entry.grid(row=0, column=1)

        tk.Label(form_frame, text="Max Credits:").grid(row=1, column=0, sticky='e')
        cp_entry = tk.Entry(form_frame)
        cp_entry.grid(row=1, column=1)

        tk.Label(form_frame, text="Start Semester (WS/SS):").grid(row=2, column=0, sticky='e')
        semester_cb = ttk.Combobox(form_frame, values=["WS", "SS"])
        semester_cb.grid(row=2, column=1)

        def save_program():
            try:
                pname = name_entry.get().strip()
                max_cp = int(cp_entry.get())
                semester = semester_cb.get().strip().upper()
                if not pname or semester not in ["WS", "SS"]:
                    raise ValueError("Invalid input.")
                if pname in programs:
                    raise ValueError("Program already exists.")
                programs[pname] = {"max_credits": max_cp, "start_semester": semester}
                save_programs(programs)
                messagebox.showinfo("Success", f"Program '{pname}' added.")
                refresh_list()
            except Exception as e:
                messagebox.showerror("Invalid Input", str(e))

        tk.Button(popup, text="Add Program", command=save_program).pack(pady=10)

    def show_all_students(self):
        popup = tk.Toplevel(self.root)
        popup.title("All HIS Students")
        popup.geometry("500x300")

        if os.path.exists("students.json"):
            with open("students.json", "r") as f:
                students = json.load(f)
        else:
            students = []

        text = tk.Text(popup, wrap='word')
        text.pack(expand=True, fill='both')
        for s in students:
            info = f"Name: {s['name']}, ID: {s['id']}, Programs: {', '.join(s['study_programs'])}, Credits: {s['credits']}\n"
            text.insert(tk.END, info)
        text.config(state='disabled')

    def clear_fields(self):
        self.name_entry.delete(0, tk.END)
        self.id_entry.delete(0, tk.END)
        self.study_entry.delete(0, tk.END)
        self.credits_entry.delete(0, tk.END)

if __name__ == '__main__':
    root = tk.Tk()
    app = HISProducerGUI(root)
    root.mainloop()
