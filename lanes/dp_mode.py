# softcable/lanes/dp_mode.py

import glob


def detect_dp_lanes() -> int | None:
    """
    Try to infer DisplayPort lane count from DRM sysfs.
    Returns 2, 4, or None if unknown.
    """
    # Very heuristic: look for DP-* connectors with "max_link_lanes"
    for path in glob.glob("/sys/class/drm/card*/DP-*/max_link_lanes"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read().strip()
            lanes = int(raw)
            if lanes in (2, 4):
                return lanes
        except (FileNotFoundError, PermissionError, OSError, ValueError):
            continue
    return None
