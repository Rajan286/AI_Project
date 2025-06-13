import tkinter as tk
import json
import os
from peregos_consumer import PeregosReceiver

DATA_FILE = "peregos_data.json"

class PeregosGUI:
    def __init__(self, root):
        self.root = root
        root.title("Peregos")

        self.text = tk.Text(root, height=20, width=60)
        self.text.pack(padx=10, pady=10)

        # 🛠: Callback verzögert, um nach Speicherzeit zu laden
        self.receiver = PeregosReceiver(callback=lambda _: self.root.after(200, self.refresh_display))
        self.receiver.start_listening()

    def refresh_display(self):
        self.text.delete("1.0", tk.END)
        if not os.path.exists(DATA_FILE):
            return

        try:
            with open(DATA_FILE, "r") as f:
                entries = json.load(f)
                if not isinstance(entries, list) or not entries:
                    return

                data = entries[-1]
                self.text.insert(tk.END, "\n--- New Student Record ---\n")
                self.text.insert(tk.END, f"Name: {data.get('name')}\n")
                self.text.insert(tk.END, f"Student ID: {data.get('id')}\n")
                self.text.insert(tk.END, f"Enrolled Programs: {', '.join(data.get('study_programs', []))}\n")
                self.text.insert(tk.END, "-----------------------------\n")

        except Exception as e:
            self.text.insert(tk.END, f"⚠️ Error loading student data: {e}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = PeregosGUI(root)
    root.mainloop()
