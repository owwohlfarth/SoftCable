import os
import time

POWER_PATH = "/sys/class/power_supply/"

def read_power_values():
    """Reads voltage, current, and wattage from any USB/Type‑C power supply."""
    voltage = None
    current = None

    try:
        for item in os.listdir(POWER_PATH):
            item_path = os.path.join(POWER_PATH, item)

            # Look for USB or Type‑C power devices
            if "usb" in item.lower() or "typec" in item.lower() or "pd" in item.lower():
                v_path = os.path.join(item_path, "voltage_now")
                c_path = os.path.join(item_path, "current_now")

                if os.path.exists(v_path):
                    with open(v_path, "r") as f:
                        voltage = int(f.read().strip()) / 1_000_000  # µV → V

                if os.path.exists(c_path):
                    with open(c_path, "r") as f:
                        current = int(f.read().strip()) / 1_000_000  # µA → A

                break

        if voltage is None or current is None:
            return None

        wattage = round(voltage * current, 2)

        return {
            "voltage": round(voltage, 3),
            "current": round(current, 3),
            "wattage": wattage
        }

    except Exception as e:
        return {"error": str(e)}
