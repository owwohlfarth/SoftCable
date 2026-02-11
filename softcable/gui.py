import tkinter as tk
from tkinter import ttk, filedialog
import os
import threading
import time

# === Existing backend imports (unchanged) ===
from softcable.usb_reader import detect_usb_c
from softcable.data_test import run_speed_test
from softcable.power_test import read_power_values
from softcable.stability_test import run_stability_test
from softcable.raw_data import get_raw_data
from softcable.cable_identity import get_cable_info
from softcable.export_txt import generate_report

# === New Phase 8 import ===
from softcable.lanes import get_lane_summary


class SoftCableGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SoftCable - USB-C Cable Tester")
        self.root.geometry("950x720")

        self.base_mount_dir = "/run/media/"
        self.power_running = False

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)

        # === Tab order (Option C) ===
        self.create_overview_tab()
        self.create_lanes_tab()          # NEW PHASE 8 TAB
        self.create_data_tab()
        self.create_power_tab()
        self.create_stability_tab()
        self.create_raw_tab()
        self.create_identity_tab()
        self.create_export_tab()

    # ============================================================
    #  PHASE 1 — OVERVIEW
    # ============================================================
    def create_overview_tab(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Overview")

        ttk.Label(frame, text="Cable Overview", font=("Arial", 16)).pack(pady=10)

        self.info_text = tk.Text(frame, height=18, width=90)
        self.info_text.pack(pady=10)

        ttk.Button(frame, text="Refresh", command=self.refresh_overview).pack()

    def refresh_overview(self):
        info = detect_usb_c()
        self.info_text.delete("1.0", tk.END)

        if info is None:
            self.info_text.insert(tk.END, "No USB-C device detected.\n")
            return

        self.info_text.insert(tk.END, f"USB-C Port: {info.port}\n")
        self.info_text.insert(tk.END, f"Partner Device: {info.partner}\n")
        self.info_text.insert(tk.END, f"Power Delivery Supported: {info.pd_supported}\n")
        self.info_text.insert(tk.END, f"PD Profiles: {info.pd_profiles}\n\n")
        self.info_text.insert(tk.END, f"Voltage: {info.voltage} V\n")
        self.info_text.insert(tk.END, f"Current: {info.current} A\n")
        self.info_text.insert(tk.END, f"Wattage: {info.wattage} W\n")

    # ============================================================
    #  PHASE 8 — LANES (NEW)
    # ============================================================
    def create_lanes_tab(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Lanes")

        ttk.Label(frame, text="USB‑C Lane Visualizer (Phase 8 – LiveScope)",
                  font=("Arial", 16)).pack(pady=10)

        self.lanes_output = tk.Text(frame, height=20, width=90)
        self.lanes_output.pack(pady=10)

        ttk.Button(frame, text="Refresh Lanes", command=self.refresh_lanes).pack()

    def refresh_lanes(self):
        self.lanes_output.delete("1.0", tk.END)

        summary = get_lane_summary()

        self.lanes_output.insert(tk.END, f"Port: {summary.get('port')}\n")
        self.lanes_output.insert(tk.END, f"Mode: {summary.get('mode')}\n")
        self.lanes_output.insert(tk.END, f"Power Role: {summary.get('power_role')}\n")
        self.lanes_output.insert(tk.END, f"Data Role: {summary.get('data_role')}\n\n")

        lanes = summary.get("lanes", ["unknown"] * 4)

        for i, lane in enumerate(lanes, start=1):
            self.lanes_output.insert(tk.END, f"Lane {i}: {lane}\n")

    # ============================================================
    #  PHASE 2 — DATA TEST
    # ============================================================
    def create_data_tab(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Data Test")

        ttk.Label(frame, text="Data Speed Test", font=("Arial", 16)).pack(pady=10)

        ttk.Label(frame, text="Detected USB Drives:").pack()
        self.drive_var = tk.StringVar()
        self.drive_dropdown = ttk.Combobox(frame, textvariable=self.drive_var, width=70)
        self.drive_dropdown.pack(pady=5)

        ttk.Button(frame, text="Refresh Drives", command=self.refresh_drives).pack(pady=5)

        ttk.Label(frame, text="Or select a path manually:").pack()
        self.path_entry = ttk.Entry(frame, width=70)
        self.path_entry.pack(pady=5)

        ttk.Button(frame, text="Browse", command=self.browse_path).pack()
        ttk.Button(frame, text="Run Test", command=self.run_data_test).pack(pady=10)

        self.data_output = tk.Text(frame, height=15, width=90)
        self.data_output.pack(pady=10)

        self.refresh_drives()

    def refresh_drives(self):
        drives = []

        if os.path.exists(self.base_mount_dir):
            for user_folder in os.listdir(self.base_mount_dir):
                user_path = os.path.join(self.base_mount_dir, user_folder)

                if os.path.isdir(user_path):
                    for entry in os.listdir(user_path):
                        full_path = os.path.join(user_path, entry)
                        if os.path.isdir(full_path):
                            drives.append(full_path)

        self.drive_dropdown["values"] = drives

        if drives:
            self.drive_dropdown.current(0)
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, drives[0])
        else:
            self.drive_dropdown.set("")
            self.path_entry.delete(0, tk.END)

    def browse_path(self):
        initial_dir = self.base_mount_dir
        if not os.path.exists(initial_dir):
            initial_dir = "/"

        path = filedialog.askdirectory(initialdir=initial_dir)

        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def run_data_test(self):
        path = self.path_entry.get().strip()
        self.data_output.delete("1.0", tk.END)

        if not path:
            self.data_output.insert(tk.END, "Please select a valid USB drive.\n")
            return

        result = run_speed_test(path)

        if result["error"]:
            self.data_output.insert(tk.END, f"Error: {result['error']}\n")
            return

        for i, run in enumerate(result["runs"], start=1):
            self.data_output.insert(
                tk.END,
                f"Run {i}: Write {run['write']} MB/s | Read {run['read']} MB/s\n"
            )

        self.data_output.insert(tk.END, "\n")
        self.data_output.insert(tk.END, f"Average Write Speed: {result['avg_write']} MB/s\n")
        self.data_output.insert(tk.END, f"Average Read Speed: {result['avg_read']} MB/s\n")

    # ============================================================
    #  PHASE 3 — POWER TEST
    # ============================================================
    def create_power_tab(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Power Test")

        ttk.Label(frame, text="Live Power Monitoring", font=("Arial", 16)).pack(pady=10)

        self.power_output = tk.Text(frame, height=15, width=90)
        self.power_output.pack(pady=10)

        ttk.Button(frame, text="Start Monitoring", command=self.start_power_test).pack(pady=5)
        ttk.Button(frame, text="Stop Monitoring", command=self.stop_power_test).pack(pady=5)

    def start_power_test(self):
        if not self.power_running:
            self.power_running = True
            threading.Thread(target=self.power_loop, daemon=True).start()

    def stop_power_test(self):
        self.power_running = False

    def power_loop(self):
        readings = []

        while self.power_running:
            data = read_power_values()

            if data is None:
                self.power_output.insert(tk.END, "No power data available.\n")
                time.sleep(1)
                continue

            if "error" in data:
                self.power_output.insert(tk.END, f"Error: {data['error']}\n")
                break

            voltage = data["voltage"]
            current = data["current"]
            wattage = data["wattage"]

            readings.append(wattage)
            if len(readings) > 20:
                readings.pop(0)

            stability = round(max(readings) - min(readings), 2)

            self.power_output.insert(
                tk.END,
                f"V: {voltage} V | I: {current} A | W: {wattage} W | Stability: {stability} W\n"
            )
            self.power_output.see(tk.END)

            time.sleep(1)

    # ============================================================
    #  PHASE 4 — STABILITY TEST
    # ============================================================
    def create_stability_tab(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Stability Test")

        ttk.Label(frame, text="Cable Stability Test", font=("Arial", 16)).pack(pady=10)

        ttk.Label(frame, text="Select USB Drive:").pack()
        self.stab_path_entry = ttk.Entry(frame, width=70)
        self.stab_path_entry.pack(pady=5)

        ttk.Button(frame, text="Use Data Test Path", command=self.copy_data_path).pack(pady=5)
        ttk.Button(frame, text="Run Stability Test", command=self.run_stability).pack(pady=10)

        self.stab_output = tk.Text(frame, height=15, width=90)
        self.stab_output.pack(pady=10)

    def copy_data_path(self):
        self.stab_path_entry.delete(0, tk.END)
        self.stab_path_entry.insert(0, self.path_entry.get())

    def run_stability(self):
        path = self.stab_path_entry.get().strip()
        self.stab_output.delete("1.0", tk.END)

        if not path:
            self.stab_output.insert(tk.END, "Please select a valid USB drive.\n")
            return

        result = run_stability_test(path)

        if result["error"]:
            self.stab_output.insert(tk.END, f"Error: {result['error']}\n")
            return

        for i, run in enumerate(result["runs"], start=1):
            self.stab_output.insert(
                tk.END,
                f"Run {i}: Write {run['write']} MB/s | Read {run['read']} MB/s\n"
            )

        self.stab_output.insert(tk.END, "\n")
        self.stab_output.insert(tk.END, f"Write Variance: {result['write_var']} MB/s\n")
        self.stab_output.insert(tk.END, f"Read Variance: {result['read_var']} MB/s\n")
        self.stab_output.insert(tk.END, f"Stability Score: {result['score']}/100\n")

    # ============================================================
    #  PHASE 5 — RAW DATA
    # ============================================================
    def create_raw_tab(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Raw Data")

        ttk.Label(frame, text="Raw USB/PD System Data", font=("Arial", 16)).pack(pady=10)

        ttk.Button(frame, text="Refresh Raw Data", command=self.refresh_raw).pack(pady=5)

        self.raw_output = tk.Text(frame, height=25, width=100)
        self.raw_output.pack(pady=10)

    def refresh_raw(self):
        self.raw_output.delete("1.0", tk.END)

        data = get_raw_data()

        for section, content in (data or {}).items():
            self.raw_output.insert(tk.END, f"=== {section.upper()} ===\n\n")

            if content is None:
                self.raw_output.insert(tk.END, "No data available.\n\n")
                continue

            for item, values in content.items():
                self.raw_output.insert(tk.END, f"[{item}]\n")
                if values:
                    for key, val in values.items():
                        self.raw_output.insert(tk.END, f"  {key}: {val}\n")
                self.raw_output.insert(tk.END, "\n")

    # ============================================================
    #  PHASE 6 — CABLE IDENTITY
    # ============================================================
    def create_identity_tab(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Cable Identity")

        ttk.Label(frame, text="USB‑C Cable Identity & E‑Marker", font=("Arial", 16)).pack(pady=10)

        ttk.Button(frame, text="Refresh Cable Info", command=self.refresh_identity).pack(pady=5)

        self.identity_output = tk.Text(frame, height=25, width=100)
        self.identity_output.pack(pady=10)

    def refresh_identity(self):
        self.identity_output.delete("1.0", tk.END)

        data = get_cable_info()

        if not data:
            self.identity_output.insert(tk.END, "No cable identity data found.\n")
            self.identity_output.insert(
                tk.END,
                "\nIf you are using a Thunderbolt 3 / USB4 cable, this usually means the "
                "laptop firmware or kernel is not exposing the cable's e‑marker over "
                "/sys/class/typec, even though the cable itself does have one.\n"
            )
            return

        for cable, info in data.items():
            self.identity_output.insert(tk.END, f"=== {cable} ===\n")

            if "note" in info:
                self.identity_output.insert(tk.END, f"  {info['note']}\n")
                self.identity_output.insert(
                    tk.END,
                    "  This usually means: cable present, but the platform is not exposing "
                    "the e‑marker contents to Linux.\n\n"
                )
                continue

            identity = info.get("identity", None)

            for key, val in info.items():
                if key == "identity":
                    continue
                self.identity_output.insert(tk.END, f"  {key}: {val}\n")

            if identity:
                self.identity_output.insert(tk.END, "  [Identity Block]\n")
                for id_key, id_val in identity.items():
                    self.identity_output.insert(tk.END, f"    {id_key}: {id_val}\n")
            else:
                self.identity_output.insert(
                    tk.END,
                    "  No identity block exposed.\n"
                    "  This cable is likely e‑marked, but the firmware is not publishing "
                    "its identity details to /sys/class/typec.\n"
                )

            self.identity_output.insert(tk.END, "\n")

    # ============================================================
    #  PHASE 7 — EXPORT
    # ============================================================
    def create_export_tab(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Export")

        ttk.Label(frame, text="Export SoftCable Report as .txt", font=("Arial", 16)).pack(pady=10)

        ttk.Label(frame, text="Data Test Path (optional):").pack()
        self.export_data_entry = ttk.Entry(frame, width=70)
        self.export_data_entry.pack(pady=5)

        ttk.Button(frame, text="Use Data Test Path", command=self.fill_export_data_path).pack(pady=5)

        ttk.Label(frame, text="Stability Test Path (optional):").pack()
        self.export_stab_entry = ttk.Entry(frame, width=70)
        self.export_stab_entry.pack(pady=5)

        ttk.Button(frame, text="Use Stability Test Path", command=self.fill_export_stab_path).pack(pady=5)

        ttk.Button(frame, text="Export Report as .txt", command=self.export_report).pack(pady=15)

        self.export_output = tk.Text(frame, height=10, width=90)
        self.export_output.pack(pady=10)

    def fill_export_data_path(self):
        self.export_data_entry.delete(0, tk.END)
        self.export_data_entry.insert(0, self.path_entry.get())

    def fill_export_stab_path(self):
        self.export_stab_entry.delete(0, tk.END)
        self.export_stab_entry.insert(0, self.stab_path_entry.get())

    def export_report(self):
        self.export_output.delete("1.0", tk.END)

        export_file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Save SoftCable Report"
        )

        if not export_file:
            self.export_output.insert(tk.END, "Export cancelled.\n")
            return

        data_path = self.export_data_entry.get().strip() or None
        stab_path = self.export_stab_entry.get().strip() or None

        try:
            path = generate_report(export_file, data_test_path=data_path, stability_path=stab_path)
            self.export_output.insert(tk.END, f"Report exported to:\n{path}\n")
        except Exception as e:
            self.export_output.insert(tk.END, f"Error exporting report: {e}\n")


# ============================================================
#  ENTRY POINT
# ============================================================
def launch_gui():
    root = tk.Tk()
    SoftCableGUI(root)
    root.mainloop()
