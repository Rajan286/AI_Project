import tkinter as tk
import json
import os
from wiseflow_consumer import WyseFlowReceiver

DATA_FILE = "wyseflow_data.json"

class WyseFlowGUI:
    def __init__(self, root):
        self.root = root
        root.title("WyseFlow")

        self.show_all_var = tk.IntVar(value=0)

        self.text = tk.Text(root, height=20, width=60)
        self.text.pack(padx=10, pady=(10, 0))

        self.checkbox = tk.Checkbutton(
            root,
            text="Show all study programs with credits",
            variable=self.show_all_var,
            command=self.refresh_display
        )
        self.checkbox.pack(pady=(5, 10))

        # 🛠: Verzögertes Nachladen nach Empfang
        self.receiver = WyseFlowReceiver(callback=lambda _: self.root.after(200, self.refresh_display))
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

                self.text.insert(tk.END, "\n--- New Application Received ---\n")
                self.text.insert(tk.END, f"Name: {data.get('name')}\n")
                self.text.insert(tk.END, f"Student ID: {data.get('id')}\n")

                if self.show_all_var.get() and isinstance(data.get("study_programs"), list) and isinstance(data.get("credits"), list):
                    for i, (prog, credit) in enumerate(zip(data["study_programs"], data["credits"]), 1):
                        self.text.insert(tk.END, f"{i}. {prog} – {credit} credits\n")
                else:
                    prog = data.get("study_programs", [""])[0]
                    cred = data.get("credits", [""])[0]
                    self.text.insert(tk.END, f"Study Program: {prog}\n")
                    self.text.insert(tk.END, f"Credits Earned: {cred}\n")

                self.text.insert(tk.END, "----------------------------------\n")

        except Exception as e:
            self.text.insert(tk.END, f"⚠️ Could not load application: {e}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = WyseFlowGUI(root)
    root.mainloop()
