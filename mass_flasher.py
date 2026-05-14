import os
import shutil
import threading
import time
import platform
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

class MicrobitFlasherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Micro:bit Mass Flasher")
        self.root.geometry("450x250")
        self.root.resizable(False, False)

        self.hex_file_path = None
        
        # UI Elements
        self.title_label = tk.Label(root, text="Micro:bit Mass Flasher", font=("Helvetica", 16, "bold"))
        self.title_label.pack(pady=10)

        self.instruction_label = tk.Label(root, text="1. Plug in all your micro:bits via USB.\n2. Select your .hex file to begin flashing.")
        self.instruction_label.pack(pady=5)

        self.select_btn = tk.Button(root, text="Select .hex File & Flash", command=self.select_and_flash, font=("Helvetica", 12), bg="#00C853", fg="white")
        self.select_btn.pack(pady=15)

        self.status_var = tk.StringVar()
        self.status_var.set("Waiting for file...")
        self.status_label = tk.Label(root, textvariable=self.status_var, fg="gray")
        self.status_label.pack(pady=5)
        
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=5)

    def find_microbits(self):
        """Finds all connected micro:bit drives based on the operating system."""
        drives = []
        os_type = platform.system()

        if os_type == "Windows":
            import string
            # Check all available drive letters on Windows
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                # micro:bits always contain a DETAILS.TXT file
                if os.path.exists(os.path.join(drive_path, "DETAILS.TXT")):
                    drives.append(drive_path)
                    
        elif os_type == "Darwin": # macOS
            volumes_path = "/Volumes"
            if os.path.exists(volumes_path):
                for vol in os.listdir(volumes_path):
                    # Look for volumes named MICROBIT
                    if "MICROBIT" in vol.upper():
                        drives.append(os.path.join(volumes_path, vol))
                        
        elif os_type == "Linux":
            # Linux usually mounts in /media/username/
            user = os.environ.get("USER")
            media_path = f"/media/{user}"
            if os.path.exists(media_path):
                for vol in os.listdir(media_path):
                    if "MICROBIT" in vol.upper():
                        drives.append(os.path.join(media_path, vol))

        return drives

    def select_and_flash(self):
        self.hex_file_path = filedialog.askopenfilename(
            title="Select Micro:bit .hex file",
            filetypes=(("Hex files", "*.hex"), ("All files", "*.*"))
        )
        
        if not self.hex_file_path:
            return # User canceled

        microbits = self.find_microbits()
        
        if not microbits:
            messagebox.showwarning("No Devices", "No micro:bits detected! Please ensure they are plugged in.")
            self.status_var.set("No micro:bits found.")
            return

        self.status_var.set(f"Found {len(microbits)} micro:bits. Flashing...")
        self.select_btn.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.progress["maximum"] = len(microbits)

        # Run the flashing in a separate thread so the GUI doesn't freeze
        threading.Thread(target=self.flash_devices, args=(microbits,), daemon=True).start()

    def flash_devices(self, microbits):
        success_count = 0
        
        for index, drive in enumerate(microbits):
            try:
                # The shutil.copy2 command mimics a drag-and-drop action
                destination = os.path.join(drive, os.path.basename(self.hex_file_path))
                shutil.copy2(self.hex_file_path, destination)
                success_count += 1
            except Exception as e:
                print(f"Failed to flash {drive}: {e}")
            
            # Update progress bar safely from thread
            self.root.after(0, self.update_progress, index + 1)
            
        self.root.after(0, self.finish_flashing, success_count, len(microbits))

    def update_progress(self, value):
        self.progress["value"] = value

    def finish_flashing(self, success, total):
        self.select_btn.config(state=tk.NORMAL)
        self.status_var.set(f"Finished! Successfully flashed {success}/{total} devices.")
        messagebox.showinfo("Complete", f"Flashing complete!\n{success} out of {total} micro:bits updated.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MicrobitFlasherApp(root)
    root.mainloop()