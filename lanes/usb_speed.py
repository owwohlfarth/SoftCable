# softcable/lanes/usb_speed.py

import glob


def get_usb_speeds() -> list[float]:
    """Return a list of observed USB link speeds in Gbit/s."""
    speeds = []
    for path in glob.glob("/sys/bus/usb/devices/*/speed"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read().strip()
            if not raw:
                continue
            val = float(raw)
            # Convert to Gbit/s where appropriate (USB reports in Mb/s)
            if val > 100:  # assume Mb/s
                speeds.append(val / 1000.0)
            else:
                speeds.append(val)
        except (FileNotFoundError, PermissionError, OSError, ValueError):
            continue
    return speeds
