import sqlite3
import time
import csv
import os
from datetime import datetime

os.makedirs('data', exist_ok=True)
DB_PATH = 'data/factory.db'
CSV_PATH = 'factory_data.csv'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS machine_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            machine_id TEXT,
            status TEXT,
            parts_produced INTEGER,
            cycle_time_sec REAL,
            alarm_code TEXT,
            downtime_reason TEXT
        )
    ''')
    conn.commit()
    conn.close()

def simulate_machines():
    with open(CSV_PATH, mode='r') as file:
        dataset = list(csv.DictReader(file))

    parts = {'M1_ComponentMounter': 0, 'M2_ReflowOven': 0, 'M3_AOI_Scanner': 0}
    
    print(f"Dataset Simulator started! Playing back {len(dataset)} rows...")
    
    while True:
        for row in dataset:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            current_time = row['timestamp'] 
            
            machines_data = [
                ('M1_ComponentMounter', row['m1_status'], row['m1_reason'], row['m1_cycle']),
                ('M2_ReflowOven', row['m2_status'], row['m2_reason'], row['m2_cycle']),
                ('M3_AOI_Scanner', row['m3_status'], row['m3_reason'], row['m3_cycle'])
            ]
            
            for m_id, status, reason, cycle in machines_data:
                if status == 'RUNNING':
                    parts[m_id] += 1
                    alarm = None
                else:
                    alarm = 'ALM_01'
                    if not reason: reason = "Unknown Fault"
                
                cursor.execute('''
                    INSERT INTO machine_events (timestamp, machine_id, status, parts_produced, cycle_time_sec, alarm_code, downtime_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (current_time, m_id, status, parts[m_id], float(cycle), alarm, reason))
            
            conn.commit()
            conn.close()
            
            print(f"[{current_time}] M1: {row['m1_status']} | M2: {row['m2_status']} | M3: {row['m3_status']}")
            time.sleep(2) 

if __name__ == "__main__":
    init_db()
    simulate_machines()