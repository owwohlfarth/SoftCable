# softcable/lanes/typec_reader.py

import os

TYPEC_CLASS_PATH = "/sys/class/typec"


def _read_file(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def get_typec_ports() -> list[str]:
    if not os.path.isdir(TYPEC_CLASS_PATH):
        return []
    entries = []
    for name in os.listdir(TYPEC_CLASS_PATH):
        full = os.path.join(TYPEC_CLASS_PATH, name)
        if os.path.isdir(full) and name.startswith("port"):
            entries.append(full)
    return sorted(entries)


def get_port_mode(port_path: str) -> str | None:
    # Common file names: current_mode, data_role, power_role, usb_typec_mode
    for candidate in ("current_mode", "usb_typec_mode", "mode"):
        value = _read_file(os.path.join(port_path, candidate))
        if value:
            return value
    return None


def get_power_role(port_path: str) -> str | None:
    return _read_file(os.path.join(port_path, "power_role"))


def get_data_role(port_path: str) -> str | None:
    return _read_file(os.path.join(port_path, "data_role"))
