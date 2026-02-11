import os

TYPEC_PATH = "/sys/class/typec/"

def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except:
        return None


def decode_identity(folder):
    """Decode the identity file inside a cable folder."""
    identity_path = os.path.join(folder, "identity")
    if not os.path.exists(identity_path):
        return None

    data = {}

    for item in os.listdir(identity_path):
        full = os.path.join(identity_path, item)
        if os.path.isfile(full):
            data[item] = read_file(full)

    return data


def decode_cable(folder):
    """Decode cable capabilities."""
    data = {}

    # Basic cable info (these may exist even without identity)
    for item in ["active", "plug_type", "speed", "current_capability", "type"]:
        path = os.path.join(folder, item)
        if os.path.exists(path):
            data[item] = read_file(path)

    # Identity block (only if present)
    identity = decode_identity(folder)
    if identity:
        data["identity"] = identity
    else:
        data["identity"] = None  # Explicitly mark as missing

    return data


def get_cable_info():
    """
    Scan all Type‑C ports and return cable info.

    Cases:
    - No /sys/class/typec/      -> return None
    - Port has no cable/        -> skipped
    - Port has cable/plug*/     -> decode each plug
    - Port has cable/ but no plug*/identity -> we still report cable present, no identity
    """
    if not os.path.exists(TYPEC_PATH):
        return None

    result = {}

    for port in os.listdir(TYPEC_PATH):
        port_path = os.path.join(TYPEC_PATH, port)

        if not os.path.isdir(port_path) or not port.startswith("port"):
            continue

        cable_path = os.path.join(port_path, "cable")
        if not os.path.exists(cable_path):
            continue

        plugs = [p for p in os.listdir(cable_path)
                 if os.path.isdir(os.path.join(cable_path, p))]

        if not plugs:
            # Cable folder exists but no plug subfolders
            result[f"{port}"] = {
                "note": "Cable folder present, but no plug/identity entries exposed by firmware."
            }
            continue

        for plug in plugs:
            plug_path = os.path.join(cable_path, plug)
            info = decode_cable(plug_path)

            key = f"{port}/{plug}"
            result[key] = info

    return result if result else None
