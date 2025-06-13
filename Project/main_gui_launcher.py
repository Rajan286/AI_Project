import tkinter as tk
import subprocess
import sys
import os

class MainLauncher:
    def __init__(self, root):
        self.root = root
        root.title("Academic Systems Launcher")

        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        tk.Label(root, text="Launch one of the systems:").pack(pady=10)

        tk.Button(root, text="HIS – Register Student", width=30, command=self.launch_his).pack(pady=5)
        tk.Button(root, text="Peregos", width=30, command=self.launch_peregos).pack(pady=5)
        tk.Button(root, text="WyseFlow", width=30, command=self.launch_wyseflow).pack(pady=5)

    def launch_his(self):
        path = os.path.join(self.base_dir, "his_producer_gui.py")
        subprocess.Popen([sys.executable, path])

    def launch_peregos(self):
        path = os.path.join(self.base_dir, "peregos_gui.py")
        subprocess.Popen([sys.executable, path])

    def launch_wyseflow(self):
        path = os.path.join(self.base_dir, "wiseflow_gui.py")
        subprocess.Popen([sys.executable, path])

if __name__ == "__main__":
    root = tk.Tk()
    app = MainLauncher(root)
    root.mainloop()
