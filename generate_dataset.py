import csv
import random
from datetime import datetime, timedelta

NUM_ROWS = 1500
start_time = datetime.now() - timedelta(hours=8)

# ECE SCENARIOS
m1_faults = ["Feeder Jam", "Vacuum Nozzle Clogged", "Component Reel Empty", "Vision Alignment Error", "Operator Break"]
m2_faults = ["Heating Zone Failure", "Conveyor Belt Stalled", "Temperature Out of Spec", "Cooling Fan Fault", "Shift Handover"]
m3_faults = ["Camera Calibration Error", "Lighting Module Failure", "Software Timeout", "Conveyor Sensor Blocked", "Quality Check Required"]

data = []
current_time = start_time

m1_down = 0
m2_down = 0
m3_down = 0
m1_reason = ""
m2_reason = ""
m3_reason = ""

for i in range(NUM_ROWS):
    current_time += timedelta(seconds=12) 
    
    # MACHINE 1 (Component Mounter)
    if m1_down > 0:
        m1_status, m1_fault = "DOWN", m1_reason
        m1_down -= 1
    elif random.random() < 0.05: 
        m1_status, m1_fault = "DOWN", random.choice(m1_faults)
        m1_down = random.randint(5, 15)
        m1_reason = m1_fault
    else:
        m1_status, m1_fault = "RUNNING", ""

    # MACHINE 2 (Reflow Oven) - Linked to M1
    if m1_status == "DOWN":
        m2_status, m2_fault = "DOWN", "Starved (Waiting for M1)"
    elif m2_down > 0:
        m2_status, m2_fault = "DOWN", m2_reason
        m2_down -= 1
    elif random.random() < 0.04:
        m2_status, m2_fault = "DOWN", random.choice(m2_faults)
        m2_down = random.randint(3, 10)
        m2_reason = m2_fault
    else:
        m2_status, m2_fault = "RUNNING", ""

    # MACHINE 3 (AOI Scanner) - Linked to M2
    if m2_status == "DOWN":
        m3_status, m3_fault = "DOWN", "Blocked (Waiting for M2)"
    elif m3_down > 0:
        m3_status, m3_fault = "DOWN", m3_reason
        m3_down -= 1
    elif random.random() < 0.03:
        m3_status, m3_fault = "DOWN", random.choice(m3_faults)
        m3_down = random.randint(2, 8)
        m3_reason = m3_fault
    else:
        m3_status, m3_fault = "RUNNING", ""

    m1_cycle = round(random.uniform(15.0, 18.0), 2) if m1_status == "RUNNING" else 0.0
    m2_cycle = round(random.uniform(25.0, 30.0), 2) if m2_status == "RUNNING" else 0.0
    m3_cycle = round(random.uniform(10.0, 12.0), 2) if m3_status == "RUNNING" else 0.0

    data.append([
        current_time.strftime("%Y-%m-%d %H:%M:%S"),
        m1_status, m1_fault, m1_cycle,
        m2_status, m2_fault, m2_cycle,
        m3_status, m3_fault, m3_cycle
    ])

with open('factory_data.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["timestamp", "m1_status", "m1_reason", "m1_cycle", "m2_status", "m2_reason", "m2_cycle", "m3_status", "m3_reason", "m3_cycle"])
    writer.writerows(data)

print("Successfully generated 1,500 rows of Electronics Assembly data!")