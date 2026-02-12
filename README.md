V1.1.0
# SoftCable – USB‑C Cable & Port Diagnostic Suite

SoftCable is a Linux USB‑C diagnostic tool that analyzes:

- USB‑C port capabilities  
- Power Delivery (PD) voltage, current, and wattage  
- USB‑C cable identity (e‑marker, speed rating, current rating)  
- USB drive read/write performance  
- Cable stability under repeated load  
- Raw USB/PD sysfs data  
- Exportable diagnostic reports  

SoftCable uses `/sys/class/typec`, `/sys/class/power_supply`, and USB storage performance tests to reveal real‑world cable and port behavior.

---

## Features

### 🔌 USB‑C Overview
- Detects partner device  
- Shows PD support  
- Displays voltage, current, wattage  

### ⚡ Power Test (Live)
- Live voltage/current/wattage  
- Stability measurement  
- 1‑second updates  

### 💾 Data Speed Test
- 4‑run averaged read/write test  
- Auto‑detects USB drives  

### 🔥 Stability Test
- 10‑run stress test  
- Detects throttling, link drops, instability  
- Generates a stability score (0–100)  

### 🧬 Cable Identity (E‑Marker)
- Reads cable identity if exposed by firmware  
- Detects active/passive cables  
- Shows speed rating, current rating, manufacturer info  
- Handles cases where firmware hides identity  

### 🛠 Raw USB/PD Data
- Dumps `/sys/class/typec`  
- Dumps `/sys/class/power_supply`  
- Dumps `/sys/bus/usb/devices`  

### 📄 Export Report
- Generates a full `.txt` diagnostic report  
- Includes all tests + raw data  

---

## Installation

```bash
git clone https://github.com/TheOwn68/SoftCable.git
cd SoftCable
pip install -r requirements.txt
python3 main.py
