#!/usr/bin/env python3
"""
Initialize Sensor Server Data

This script initializes the server data files for sensor data.
"""

import pandas as pd
import os
import json
from datetime import datetime, timedelta
import numpy as np

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

def generate_sample_sensor_data():
    """Generate sample sensor data if none exists"""
    try:
        print("Generating sample sensor data")
        
        # Generate sample data
        now = datetime.now()
        times = [now - timedelta(minutes=i*10) for i in range(24)]
        
        data = {
            'timestamp': times,
            'temperature': [round(np.random.uniform(65, 75), 1) for _ in range(24)],
            'humidity': [round(np.random.uniform(30, 60), 1) for _ in range(24)],
            'battery': [100 for _ in range(24)]
        }
        
        sensor_df = pd.DataFrame(data)
        
        # Save to CSV
        sensor_df.to_csv('data/sensor_data.csv', index=False)
        
        print(f"Created sample sensor data with {len(sensor_df)} rows")
        return sensor_df
    except Exception as e:
        print(f"Error generating sample data: {str(e)}")
        return None

def save_data_json(sensor_df):
    """Save data in JSON format for the web server"""
    try:
        # Create a data structure expected by the server
        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sensor": {
                "temperature": float(sensor_df['temperature'].iloc[0]) if not sensor_df.empty else None,
                "humidity": float(sensor_df['humidity'].iloc[0]) if not sensor_df.empty else None,
                "battery": int(sensor_df['battery'].iloc[0]) if not sensor_df.empty else None
            }
        }
        
        # Save to JSON file
        with open('data/current_sensor.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print("Saved current sensor data to data/current_sensor.json")
        return True
    except Exception as e:
        print(f"Error saving JSON data: {str(e)}")
        return False

def main():
    # Generate sample sensor data
    sensor_df = generate_sample_sensor_data()
    
    if sensor_df is not None:
        # Save data in format expected by server
        save_data_json(sensor_df)
        print("Data initialization complete. Restart the sensor server.")
    else:
        print("Failed to initialize data.")

if __name__ == "__main__":
    main() 