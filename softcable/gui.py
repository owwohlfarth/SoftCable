import customtkinter as ctk
from tkinter import filedialog
import os
import threading
import time

# === Backend imports (unchanged) ===
from softcable.usb_reader import detect_usb_c
from softcable.data_test import run_speed_test
from softcable.power_test import read_power_values
from softcable.stability_test import run_stability_test
from softcable.raw_data import get_raw_data
from softcable.cable_identity import get_cable_info
from softcable.export_txt import generate_report
from softcable.lanes import get_lane_summary


class SoftCableGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SoftCable – USB‑C Cable Tester")
        self.root.geometry("1100x750")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.base_mount_dir = "/run/media/"
        self.power_running = False

        # === Top bar with theme toggle ===
        topbar = ctk.CTkFrame(self.root, height=50)
        topbar.pack(fill="x")

        ctk.CTkLabel(topbar, text="SoftCable", font=("Arial", 22, "bold")).pack(side="left", padx=20)

        self.theme_switch = ctk.CTkSegmentedButton(
            topbar,
            values=["Light", "Dark"],
            command=self.change_theme
        )
        self.theme_switch.set("Dark")
        self.theme_switch.pack(side="right", padx=20)

        # === Tab system ===
        self.tabs = ctk.CTkTabview(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self.create_overview_tab()
        self.create_lanes_tab()
        self.create_data_tab()
        self.create_power_tab()
        self.create_stability_tab()
        self.create_raw_tab()
        self.create_identity_tab()
        self.create_export_tab()

    # ============================================================
    #  THEME SWITCH
    # ============================================================
    def change_theme(self, mode):
        ctk.set_appearance_mode(mode.lower())

    # ============================================================
    #  TAB: OVERVIEW
    # ============================================================
    def create_overview_tab(self):
        tab = self.tabs.add("Overview")

        ctk.CTkLabel(tab, text="Cable Overview", font=("Arial", 18, "bold")).pack(pady=10)

        self.overview_box = ctk.CTkTextbox(tab, height=400, width=900)
        self.overview_box.pack(pady=10)
        self.overview_box.configure(state="disabled")

        ctk.CTkButton(tab, text="Refresh", command=self.refresh_overview).pack(pady=5)

    def refresh_overview(self):
        info = detect_usb_c()

        self.overview_box.configure(state="normal")
        self.overview_box.delete("1.0", "end")

        if info is None:
            self.overview_box.insert("end", "No USB‑C device detected.\n")
        else:
            self.overview_box.insert("end", f"USB‑C Port: {info.port}\n")
            self.overview_box.insert("end", f"Partner Device: {info.partner}\n")
            self.overview_box.insert("end", f"Power Delivery Supported: {info.pd_supported}\n")
            self.overview_box.insert("end", f"PD Profiles: {info.pd_profiles}\n\n")
            self.overview_box.insert("end", f"Voltage: {info.voltage} V\n")
            self.overview_box.insert("end", f"Current: {info.current} A\n")
            self.overview_box.insert("end", f"Wattage: {info.wattage} W\n")

        self.overview_box.configure(state="disabled")

    # ============================================================
    #  TAB: LANES
    # ============================================================
    def create_lanes_tab(self):
        tab = self.tabs.add("Lanes")

        ctk.CTkLabel(tab, text="USB‑C Lane Visualizer", font=("Arial", 18, "bold")).pack(pady=10)

        self.lanes_box = ctk.CTkTextbox(tab, height=400, width=900)
        self.lanes_box.pack(pady=10)
        self.lanes_box.configure(state="disabled")

        ctk.CTkButton(tab, text="Refresh Lanes", command=self.refresh_lanes).pack(pady=5)

    def refresh_lanes(self):
        summary = get_lane_summary()

        self.lanes_box.configure(state="normal")
        self.lanes_box.delete("1.0", "end")

        self.lanes_box.insert("end", f"Port: {summary.get('port')}\n")
        self.lanes_box.insert("end", f"Mode: {summary.get('mode')}\n")
        self.lanes_box.insert("end", f"Power Role: {summary.get('power_role')}\n")
        self.lanes_box.insert("end", f"Data Role: {summary.get('data_role')}\n\n")

        lanes = summary.get("lanes", ["unknown"] * 4)
        for i, lane in enumerate(lanes, start=1):
            self.lanes_box.insert("end", f"Lane {i}: {lane}\n")

        self.lanes_box.configure(state="disabled")

    # ============================================================
    #  TAB: DATA TEST
    # ============================================================
    def create_data_tab(self):
        tab = self.tabs.add("Data Test")

        ctk.CTkLabel(tab, text="Data Speed Test", font=("Arial", 18, "bold")).pack(pady=10)

        ctk.CTkLabel(tab, text="Detected USB Drives:").pack()
        self.drive_var = ctk.StringVar()
        self.drive_dropdown = ctk.CTkComboBox(tab, variable=self.drive_var, width=600)
        self.drive_dropdown.pack(pady=5)

        ctk.CTkButton(tab, text="Refresh Drives", command=self.refresh_drives).pack(pady=5)

        ctk.CTkLabel(tab, text="Or select a path manually:").pack()
        self.path_entry = ctk.CTkEntry(tab, width=600)
        self.path_entry.pack(pady=5)

        ctk.CTkButton(tab, text="Browse", command=self.browse_path).pack()
        ctk.CTkButton(tab, text="Run Test", command=self.run_data_test).pack(pady=10)

        self.data_box = ctk.CTkTextbox(tab, height=350, width=900)
        self.data_box.pack(pady=10)
        self.data_box.configure(state="disabled")

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

        self.drive_dropdown.configure(values=drives)

        if drives:
            self.drive_dropdown.set(drives[0])
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, drives[0])
        else:
            self.drive_dropdown.set("")
            self.path_entry.delete(0, "end")

    def browse_path(self):
        initial_dir = self.base_mount_dir if os.path.exists(self.base_mount_dir) else "/"
        path = filedialog.askdirectory(initialdir=initial_dir)
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)

    def run_data_test(self):
        path = self.path_entry.get().strip()

        self.data_box.configure(state="normal")
        self.data_box.delete("1.0", "end")

        if not path:
            self.data_box.insert("end", "Please select a valid USB drive.\n")
            self.data_box.configure(state="disabled")
            return

        result = run_speed_test(path)

        if result["error"]:
            self.data_box.insert("end", f"Error: {result['error']}\n")
        else:
            for i, run in enumerate(result["runs"], start=1):
                self.data_box.insert("end", f"Run {i}: Write {run['write']} MB/s | Read {run['read']} MB/s\n")

            self.data_box.insert("end", "\n")
            self.data_box.insert("end", f"Average Write Speed: {result['avg_write']} MB/s\n")
            self.data_box.insert("end", f"Average Read Speed: {result['avg_read']} MB/s\n")

        self.data_box.configure(state="disabled")

    # ============================================================
    #  TAB: POWER TEST (Live Dashboard)
    # ============================================================
    def create_power_tab(self):
        tab = self.tabs.add("Power Test")

        ctk.CTkLabel(tab, text="Live Power Monitoring", font=("Arial", 18, "bold")).pack(pady=10)

        self.voltage_label = ctk.CTkLabel(tab, text="Voltage: -- V", font=("Arial", 16))
        self.current_label = ctk.CTkLabel(tab, text="Current: -- A", font=("Arial", 16))
        self.wattage_label = ctk.CTkLabel(tab, text="Wattage: -- W", font=("Arial", 16))
        self.stability_label = ctk.CTkLabel(tab, text="Stability: -- W", font=("Arial", 16))

        self.voltage_label.pack(pady=5)
        self.current_label.pack(pady=5)
        self.wattage_label.pack(pady=5)
        self.stability_label.pack(pady=5)

        ctk.CTkButton(tab, text="Start Monitoring", command=self.start_power_test).pack(pady=10)
        ctk.CTkButton(tab, text="Stop Monitoring", command=self.stop_power_test).pack()

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

            if data is None or "error" in data:
                self.voltage_label.configure(text="Voltage: -- V")
                self.current_label.configure(text="Current: -- A")
                self.wattage_label.configure(text="Wattage: -- W")
                self.stability_label.configure(text="Stability: -- W")
                time.sleep(1)
                continue

            voltage = data["voltage"]
            current = data["current"]
            wattage = data["wattage"]

            readings.append(wattage)
            if len(readings) > 20:
                readings.pop(0)

            stability = round(max(readings) - min(readings), 2)

            self.voltage_label.configure(text=f"Voltage: {voltage} V")
            self.current_label.configure(text=f"Current: {current} A")
            self.wattage_label.configure(text=f"Wattage: {wattage} W")
            self.stability_label.configure(text=f"Stability: {stability} W")

            time.sleep(1)

    # ============================================================
    #  TAB: STABILITY TEST
    # ============================================================
    def create_stability_tab(self):
        tab = self.tabs.add("Stability Test")

        ctk.CTkLabel(tab, text="Cable Stability Test", font=("Arial", 18, "bold")).pack(pady=10)

        ctk.CTkLabel(tab, text="Select USB Drive:").pack()
        self.stab_path_entry = ctk.CTkEntry(tab, width=600)
        self.stab_path_entry.pack(pady=5)

        ctk.CTkButton(tab, text="Use Data Test Path", command=self.copy_data_path).pack(pady=5)
        ctk.CTkButton(tab, text="Run Stability Test", command=self.run_stability).pack(pady=10)

        self.stab_box = ctk.CTkTextbox(tab, height=350, width=900)
        self.stab_box.pack(pady=10)
        self.stab_box.configure(state="disabled")

    def copy_data_path(self):
        self.stab_path_entry.delete(0, "end")
        self.stab_path_entry.insert(0, self.path_entry.get())

    def run_stability(self):
        path = self.stab_path_entry.get().strip()

        self.stab_box.configure(state="normal")
        self.stab_box.delete("1.0", "end")

        if not path:
            self.stab_box.insert("end", "Please select a valid USB drive.\n")
            self.stab_box.configure(state="disabled")
            return

        result = run_stability_test(path)

        if result["error"]:
            self.stab_box.insert("end", f"Error: {result['error']}\n")
        else:
            for i, run in enumerate(result["runs"], start=1):
                self.stab_box.insert("end", f"Run {i}: Write {run['write']} MB/s | Read {run['read']} MB/s\n")

            self.stab_box.insert("end", "\n")
            self.stab_box.insert("end", f"Write Variance: {result['write_var']} MB/s\n")
            self.stab_box.insert("end", f"Read Variance: {result['read_var']} MB/s\n")
            self.stab_box.insert("end", f"Stability Score: {result['score']}/100\n")

        self.stab_box.configure(state="disabled")

    # ============================================================
    #  TAB: RAW DATA
    # ============================================================
    def create_raw_tab(self):
        tab = self.tabs.add("Raw Data")

        ctk.CTkLabel(tab, text="Raw USB/PD System Data", font=("Arial", 18, "bold")).pack(pady=10)

        ctk.CTkButton(tab, text="Refresh Raw Data", command=self.refresh_raw).pack(pady=5)

        self.raw_box = ctk.CTkTextbox(tab, height=450, width=900)
        self.raw_box.pack(pady=10)
        self.raw_box.configure(state="disabled")

    def refresh_raw(self):
        data = get_raw_data()

        self.raw_box.configure(state="normal")
        self.raw_box.delete("1.0", "end")

        for section, content in (data or {}).items():
            self.raw_box.insert("end", f"=== {section.upper()} ===\n\n")

            if content is None:
                self.raw_box.insert("end", "No data available.\n\n")
                continue

            for item, values in content.items():
                self.raw_box.insert("end", f"[{item}]\n")
                if values:
                    for key, val in values.items():
                        self.raw_box.insert("end", f"  {key}: {val}\n")
                self.raw_box.insert("end", "\n")

        self.raw_box.configure(state="disabled")

    # ============================================================
    #  TAB: CABLE IDENTITY
    # ============================================================
    def create_identity_tab(self):
        tab = self.tabs.add("Cable Identity")

        ctk.CTkLabel(tab, text="USB‑C Cable Identity & E‑Marker", font=("Arial", 18, "bold")).pack(pady=10)

        ctk.CTkButton(tab, text="Refresh Cable Info", command=self.refresh_identity).pack(pady=5)

        self.identity_box = ctk.CTkTextbox(tab, height=450, width=900)
        self.identity_box.pack(pady=10)
        self.identity_box.configure(state="disabled")

    def refresh_identity(self):
        data = get_cable_info()

        self.identity_box.configure(state="normal")
        self.identity_box.delete("1.0", "end")

        if not data:
            self.identity_box.insert("end", "No cable identity data found.\n")
            self.identity_box.insert(
                "end",
                "\nIf you are using a Thunderbolt 3 / USB4 cable, this usually means the "
                "laptop firmware or kernel is not exposing the cable's e‑marker.\n"
            )
            self.identity_box.configure(state="disabled")
            return

        for cable, info in data.items():
            self.identity_box.insert("end", f"=== {cable} ===\n")

            if "note" in info:
                self.identity_box.insert("end", f"  {info['note']}\n\n")
                continue

            identity = info.get("identity", None)

            for key, val in info.items():
                if key != "identity":
                    self.identity_box.insert("end", f"  {key}: {val}\n")

            if identity:
                self.identity_box.insert("end", "  [Identity Block]\n")
                for id_key, id_val in identity.items():
                    self.identity_box.insert("end", f"    {id_key}: {id_val}\n")
            else:
                self.identity_box.insert("end", "  No identity block exposed.\n")

            self.identity_box.insert("end", "\n")

        self.identity_box.configure(state="disabled")

    # ============================================================
    #  TAB: EXPORT
    # ============================================================
    def create_export_tab(self):
        tab = self.tabs.add("Export")

        ctk.CTkLabel(tab, text="Export SoftCable Report", font=("Arial", 18, "bold")).pack(pady=10)

        ctk.CTkLabel(tab, text="Data Test Path (optional):").pack()
        self.export_data_entry = ctk.CTkEntry(tab, width=600)
        self.export_data_entry.pack(pady=5)

        ctk.CTkButton(tab, text="Use Data Test Path", command=self.fill_export_data_path).pack(pady=5)

        ctk.CTkLabel(tab, text="Stability Test Path (optional):").pack()
        self.export_stab_entry = ctk.CTkEntry(tab, width=600)
        self.export_stab_entry.pack(pady=5)

        ctk.CTkButton(tab, text="Use Stability Test Path", command=self.fill_export_stab_path).pack(pady=5)

        ctk.CTkButton(tab, text="Export Report as .txt", command=self.export_report).pack(pady=15)

        self.export_box = ctk.CTkTextbox(tab, height=200, width=900)
        self.export_box.pack(pady=10)
        self.export_box.configure(state="disabled")

    def fill_export_data_path(self):
        self.export_data_entry.delete(0, "end")
        self.export_data_entry.insert(0, self.path_entry.get())

    def fill_export_stab_path(self):
        self.export_stab_entry.delete(0, "end")
        self.export_stab_entry.insert(0, self.stab_path_entry.get())

    def export_report(self):
        self.export_box.configure(state="normal")
        self.export_box.delete("1.0", "end")

        export_file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Save SoftCable Report"
        )

        if not export_file:
            self.export_box.insert("end", "Export cancelled.\n")
            self.export_box.configure(state="disabled")
            return

        data_path = self.export_data_entry.get().strip() or None
        stab_path = self.export_stab_entry.get().strip() or None

        try:
            path = generate_report(export_file, data_test_path=data_path, stability_path=stab_path)
            self.export_box.insert("end", f"Report exported to:\n{path}\n")
        except Exception as e:
            self.export_box.insert("end", f"Error exporting report: {e}\n")

        self.export_box.configure(state="disabled")


# ============================================================
#  ENTRY POINT
# ============================================================
def launch_gui():
    root = ctk.CTk()
    SoftCableGUI(root)
    root.mainloop()
