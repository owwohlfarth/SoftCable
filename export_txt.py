import os
import time

from softcable.usb_reader import detect_usb_c
from softcable.data_test import run_speed_test
from softcable.stability_test import run_stability_test
from softcable.power_test import read_power_values
from softcable.raw_data import get_raw_data
from softcable.cable_identity import get_cable_info


def generate_report(export_path, data_test_path=None, stability_path=None):
    """
    Generate a full SoftCable report as a .txt file.

    export_path: full path to the .txt file to write
    data_test_path: optional path for a quick 4‑run data test
    stability_path: optional path for a 10‑run stability test
    """
    lines = []

    # Header
    lines.append("SoftCable USB‑C Diagnostic Report")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    # Overview
    lines.append("[Overview]")
    info = detect_usb_c()
    if info is None:
        lines.append("  No USB‑C device detected.")
    else:
        lines.append(f"  USB‑C Port: {info.port}")
        lines.append(f"  Partner Device: {info.partner}")
        lines.append(f"  Power Delivery Supported: {info.pd_supported}")
        lines.append(f"  PD Profiles: {info.pd_profiles}")
        lines.append(f"  Voltage: {info.voltage} V")
        lines.append(f"  Current: {info.current} A")
        lines.append(f"  Wattage: {info.wattage} W")
    lines.append("")

    # Data Test (optional quick run)
    lines.append("[Data Speed Test]")
    if data_test_path:
        result = run_speed_test(data_test_path)
        if result["error"]:
            lines.append(f"  Error: {result['error']}")
        else:
            for i, run in enumerate(result["runs"], start=1):
                lines.append(
                    f"  Run {i}: Write {run['write']} MB/s | Read {run['read']} MB/s"
                )
            lines.append("")
            lines.append(f"  Average Write: {result['avg_write']} MB/s")
            lines.append(f"  Average Read: {result['avg_read']} MB/s")
    else:
        lines.append("  No data test path provided.")
    lines.append("")

    # Stability Test (optional)
    lines.append("[Stability Test]")
    if stability_path:
        result = run_stability_test(stability_path)
        if result["error"]:
            lines.append(f"  Error: {result['error']}")
        else:
            for i, run in enumerate(result["runs"], start=1):
                lines.append(
                    f"  Run {i}: Write {run['write']} MB/s | Read {run['read']} MB/s"
                )
            lines.append("")
            lines.append(f"  Write Variance: {result['write_var']} MB/s")
            lines.append(f"  Read Variance: {result['read_var']} MB/s")
            lines.append(f"  Stability Score: {result['score']}/100")
    else:
        lines.append("  No stability test path provided.")
    lines.append("")

    # One snapshot of power
    lines.append("[Power Snapshot]")
    pdata = read_power_values()
    if pdata is None:
        lines.append("  No power data available.")
    elif "error" in pdata:
        lines.append(f"  Error: {pdata['error']}")
    else:
        lines.append(f"  Voltage: {pdata['voltage']} V")
        lines.append(f"  Current: {pdata['current']} A")
        lines.append(f"  Wattage: {pdata['wattage']} W")
    lines.append("")

    # Cable Identity
    lines.append("[Cable Identity / E‑Marker]")
    cdata = get_cable_info()
    if not cdata:
        lines.append("  No cable identity data found.")
    else:
        for cable, info in cdata.items():
            lines.append(f"  === {cable} ===")
            if "note" in info:
                lines.append(f"    {info['note']}")
                continue
            identity = info.get("identity", None)
            for key, val in info.items():
                if key == "identity":
                    continue
                lines.append(f"    {key}: {val}")
            if identity:
                lines.append("    [Identity Block]")
                for id_key, id_val in identity.items():
                    lines.append(f"      {id_key}: {id_val}")
            else:
                lines.append("    No identity block exposed.")
            lines.append("")
    lines.append("")

    # Raw Data (summary dump)
    lines.append("[Raw USB/PD System Data]")
    rdata = get_raw_data()
    for section, content in (rdata or {}).items():
        lines.append(f"  === {section.upper()} ===")
        if content is None:
            lines.append("    No data available.")
            continue
        for item, values in content.items():
            lines.append(f"    [{item}]")
            if values:
                for key, val in values.items():
                    lines.append(f"      {key}: {val}")
        lines.append("")
    lines.append("")

    # Write file
    os.makedirs(os.path.dirname(export_path), exist_ok=True)
    with open(export_path, "w") as f:
        f.write("\n".join(lines))

    return export_path
