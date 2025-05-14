#!/usr/bin/env python3
import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

# Calculate the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Add the project to the Python path
sys.path.insert(0, str(BASE_DIR))

# Import the GoveeThermometerHygrometer class
from govee_h5075.govee_h5075 import GoveeThermometerHygrometer

# Setup argument parser
parser = argparse.ArgumentParser(description='Read temperature and humidity from Govee H5075 sensors')
parser.add_argument('--scan-time', type=int, default=20, help='Scan duration in seconds')
parser.add_argument('--output-file', type=str, help='Output file path (optional)')
parser.add_argument('--log', action='store_true', help='Enable detailed logging')

def sensor_consumer(address, name, battery, measurement):
    """
    Process data from discovered Govee sensors
    
    Args:
        address: Bluetooth MAC address of the sensor
        name: Device name 
        battery: Battery level
        measurement: Measurement object with temperature and humidity
    """
    data = {
        'device': address,
        'name': name,
        'temperature': round(measurement.temperatureC, 2),
        'humidity': round(measurement.relHumidity, 2),
        'timestamp': datetime.now().isoformat(),
        'battery': battery,
        'status': 'online'
    }
    
    # Additional data for debugging
    if args.log:
        data.update({
            'temperature_f': round(measurement.temperatureF, 2),
            'dew_point': round(measurement.dewPointC, 2),
            'abs_humidity': round(measurement.absHumidity, 2),
            'steam_pressure': round(measurement.steamPressure, 2)
        })
    
    # Print data to console
    print(f"Found Govee sensor {name} ({address}):")
    print(f"  Temperature: {data['temperature']}°C / {measurement.temperatureF:.2f}°F")
    print(f"  Humidity: {data['humidity']}%")
    print(f"  Battery: {battery}%")
    print(f"  Dew Point: {measurement.dewPointC:.2f}°C")
    
    # Save data to specified output file
    if args.output_file:
        output_path = args.output_file
    else:
        # Default to the current_sensor.json file in the data directory
        data_dir = os.path.join(BASE_DIR, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        output_path = os.path.join(data_dir, 'current_sensor.json')
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Sensor data saved to {output_path}")
    
    # Also save to latest_reading.json for comparison
    with open(os.path.join(os.path.dirname(output_path), 'latest_reading.json'), 'w') as f:
        json.dump(data, f, indent=2)

async def scan_for_govee_sensors(duration=20):
    """
    Scan for Govee H5075 devices and report their readings
    """
    print(f"Scanning for Govee sensors for {duration} seconds...")
    await GoveeThermometerHygrometer.scan(consumer=sensor_consumer, duration=duration)
    print("Scan complete")

def progress_callback(found):
    """Callback to show scanning progress"""
    print(f"Scanning... {found} Bluetooth devices found", end='\r')

if __name__ == "__main__":
    args = parser.parse_args()
    
    try:
        # Run the scan with the consumer callback
        asyncio.run(scan_for_govee_sensors(duration=args.scan_time))
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error scanning for sensors: {str(e)}") 