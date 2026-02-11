# softcable/lanes/lane_detector.py

from .typec_reader import get_typec_ports, get_port_mode, get_power_role, get_data_role
from .usb_speed import get_usb_speeds
from .dp_mode import detect_dp_lanes


def get_lane_summary() -> dict:
    """
    Return a high-level summary of lane usage.

    Structure:
    {
        "port": "<path or 'unknown'>",
        "mode": "<raw mode string or 'unknown'>",
        "power_role": "...",
        "data_role": "...",
        "lanes": [
            "USB 3.x",
            "USB 3.x",
            "DP Alt Mode",
            "DP Alt Mode",
        ]
    }
    """
    ports = get_typec_ports()
    if not ports:
        return {
            "port": "No /sys/class/typec ports found",
            "mode": "unknown",
            "power_role": "unknown",
            "data_role": "unknown",
            "lanes": ["unknown"] * 4,
        }

    port = ports[0]  # use first detected port
    mode = get_port_mode(port) or "unknown"
    power_role = get_power_role(port) or "unknown"
    data_role = get_data_role(port) or "unknown"

    usb_speeds = get_usb_speeds()
    max_usb = max(usb_speeds) if usb_speeds else 0.0
    dp_lanes = detect_dp_lanes()

    lanes = ["unknown"] * 4

    # Basic inference rules
    if "dfp" in data_role.lower() or "host" in data_role.lower():
        if max_usb >= 5.0:
            lanes[0] = "USB 3.x"
            lanes[1] = "USB 3.x"

    if dp_lanes == 4:
        lanes = ["DP Alt Mode"] * 4
    elif dp_lanes == 2:
        lanes[0] = "USB 3.x"
        lanes[1] = "USB 3.x"
        lanes[2] = "DP Alt Mode"
        lanes[3] = "DP Alt Mode"

    return {
        "port": port,
        "mode": mode,
        "power_role": power_role,
        "data_role": data_role,
        "lanes": lanes,
    }
