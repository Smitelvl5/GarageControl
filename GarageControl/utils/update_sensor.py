#!/usr/bin/env python
import os
import sys
import django
import asyncio
import time
from datetime import datetime, timezone
from asgiref.sync import sync_to_async
import json
import requests
from pathlib import Path

# Set up Django environment only if run as script
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "govee_control.settings")
    django.setup()

# Import Django models after setup
from garage.models import SensorData
from govee_h5075.govee_h5075 import GoveeThermometerHygrometer, Measurement
from garage.govee_client import GoveeClient

# Calculate the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Update the sys.path to include the project root
sys.path.insert(0, str(BASE_DIR))

# Known Govee H5075 device MAC address
GOVEE_MAC_ADDRESS = "A4:C1:38:80:4F:47"
GOVEE_DEVICE_NAME = "Govee_H5075_4F47"

@sync_to_async
def save_sensor_data(device_name, temperature, humidity, battery, status="online", timestamp=None):
    # Calculate additional fields if temperature and humidity are available
    dew_point = None
    abs_humidity = None
    steam_pressure = None
    
    if temperature is not None and humidity is not None:
        # Create a temporary measurement object to use its calculations
        temp_measurement = Measurement(
            timestamp=datetime.now(timezone.utc), 
            temperatureC=temperature, 
            relHumidity=humidity
        )
        dew_point = temp_measurement.dewPointC
        abs_humidity = temp_measurement.absHumidity
        steam_pressure = temp_measurement.steamPressure
    
    sensor_data = SensorData(
        device_name=device_name,
        temperature=temperature,  # Temperature in Celsius
        humidity=humidity,
        battery=battery,
        status=status,
        timestamp=timestamp,
        dew_point=dew_point,
        abs_humidity=abs_humidity,
        steam_pressure=steam_pressure
    )
    sensor_data.save()
    return sensor_data

@sync_to_async
def save_sensor_offline_status(device_name):
    """Mark a sensor as offline in the database"""
    # Get the last reading to preserve the last known values
    try:
        last_reading = SensorData.objects.filter(device_name=device_name).order_by('-timestamp').first()
        if last_reading:
            # Use last known values but mark as offline
            sensor_data = SensorData(
                device_name=device_name,
                temperature=last_reading.temperature,
                humidity=last_reading.humidity,
                battery=last_reading.battery if last_reading.battery else 0,
                status="offline"
            )
        else:
            # No previous reading, use null values
            sensor_data = SensorData(
                device_name=device_name,
                temperature=None,
                humidity=None, 
                battery=0,
                status="offline"
            )
        sensor_data.save()
        return sensor_data
    except Exception as e:
        print(f"Error saving offline status: {str(e)}")
        return None

async def handle_h5075_device(device_address, device_name, retry_attempts=3, retry_interval=2):
    """
    Connect to a Govee H5075 device and retrieve sensor data
    Now with retry logic for more robust connections
    
    Args:
        device_address: The MAC address of the device
        device_name: Name to use for the device in logs and database
        retry_attempts: Number of connection retry attempts (default 3)
        retry_interval: Seconds to wait between retries (default 2)
    """
    attempt = 0
    last_error = None
    
    while attempt < retry_attempts:
        try:
            if attempt > 0:
                print(f"Retry attempt {attempt}/{retry_attempts} for device {device_address}...")
                
            print(f"Connecting to Govee device at {device_address}...")
            
            # Create a new device object for each connection attempt
            # This avoids any lingering state from previous connection attempts
            device = GoveeThermometerHygrometer(device_address)
            
            # Check if device is already connected and disconnect if needed
            if hasattr(device, 'is_connected') and device.is_connected:
                print(f"Device appears to be connected already, disconnecting first...")
                try:
                    await device.disconnect()
                    print("Successfully disconnected previous connection")
                    # Brief pause before reconnecting
                    await asyncio.sleep(0.5)
                except Exception as disconnect_error:
                    print(f"Error disconnecting: {disconnect_error}, will still try to connect")
            
            # Attempt to connect with timeout
            connect_task = asyncio.create_task(device.connect())
            try:
                # Increased timeout for Raspberry Pi
                await asyncio.wait_for(connect_task, timeout=20.0)  # 20 second connection timeout
            except asyncio.TimeoutError:
                # If connection times out, try to cancel the task
                connect_task.cancel()
                # Wait for the cancellation to complete
                try:
                    await connect_task
                except asyncio.CancelledError:
                    print("Connection task cancelled successfully.")
                raise Exception("Connection attempt timed out after 20 seconds")
                
            # Connected successfully, now request a measurement
            print("Connected to Govee device, requesting measurement...")
            await device.requestMeasurementAndBattery()
            
            # Wait briefly for notification response - increased for Raspberry Pi
            await asyncio.sleep(4) # Increased from 2 to 4 seconds
            
            # Check if we got a measurement
            if device.measurement:
                print(f"Received measurement: Temp={device.measurement.temperatureC}°C, Humidity={device.measurement.relHumidity}%")
                
                # Save to database
                timestamp = datetime.now(timezone.utc)
                await save_sensor_data(
                    device_name=device_name,
                    temperature=device.measurement.temperatureC,
                    humidity=device.measurement.relHumidity,
                    battery=device.battery if hasattr(device, 'battery') else 0,
                    status="online",
                    timestamp=timestamp
                )
                
                # Try to disconnect cleanly 
                try:
                    await device.disconnect()
                    print("Disconnected successfully")
                except Exception as disconnect_error:
                    print(f"Warning: Error during disconnect: {disconnect_error}")
                
                return device.measurement
            else:
                # Attempt to disconnect if no measurement received to free up resources
                try:
                    if device.is_connected:
                        print("No measurement received, attempting to disconnect...")
                        await device.disconnect()
                        print("Disconnected after no measurement.")
                except Exception as disc_err:
                    print(f"Error disconnecting after no measurement: {disc_err}")
                raise Exception("No measurement received from device")
        
        except Exception as e:
            last_error = e
            print(f"Error on attempt {attempt+1}/{retry_attempts}: {str(e)}")
            
            # Try to ensure device is disconnected before retry
            try:
                if 'device' in locals() and hasattr(device, 'disconnect') and device.is_connected:
                    print(f"Cleaning up connection to {device_address} after error...")
                    await device.disconnect()
                    print(f"Cleaned up connection to {device_address}.")
            except Exception as disconnect_error:
                print(f"Error during cleanup disconnect for {device_address}: {disconnect_error}")
            
            # Wait before retrying
            if attempt + 1 < retry_attempts:
                await asyncio.sleep(retry_interval * (attempt + 1))  # Exponential backoff
            
        finally:
            attempt += 1
    
    # If we get here, all attempts failed
    print(f"All {retry_attempts} attempts failed to connect to {device_address}")
    print(f"Last error: {last_error}")
    
    # Mark sensor as offline in the database
    await save_sensor_offline_status(device_name)
    
    if last_error:
        raise last_error
    else:
        raise Exception(f"Failed to connect to device {device_address} after {retry_attempts} attempts")

async def handle_h5080_device(device_id, device_name):
    try:
        client = GoveeClient()
        state = client.get_device_state(device_id, "H5080")
        if state:
            sensor_data = await save_sensor_data(
                device_name=device_name,
                temperature=state.get('temperature', 0),
                humidity=state.get('humidity', 0),
                battery=state.get('battery', 0),
                status="online"
            )
            print(f"Updated H5080 sensor data: {sensor_data.temperature}°C, {sensor_data.humidity}%, Battery: {sensor_data.battery}%")
    except Exception as e:
        print(f"Error updating H5080 sensor data: {str(e)}")
        # Mark sensor as offline in the database
        await save_sensor_offline_status(device_name)
        print(f"Marked sensor {device_name} as offline")

# Function called by the app config to start background updates
def update_sensor_data():
    """
    This is a wrapper function that creates and runs the async event loop 
    for sensor updates when called from a non-async context.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_update_sensor_data_async())
    finally:
        loop.close()

# The actual async function that does the work
async def _update_sensor_data_async():
    """Async function that continually updates sensor data"""
    
    # Set up path for current sensor data JSON file
    data_dir = os.path.join(BASE_DIR, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    current_sensor_file = os.path.join(data_dir, 'current_sensor.json')
    
    def log_message(msg):
        """Helper to log messages with timestamp"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
    
    # On startup, make multiple attempts to connect to the Bluetooth device
    # This helps ensure we get a connection even if Bluetooth is still initializing
    startup_attempts = 5
    startup_connected = False
    
    for attempt in range(startup_attempts):
        try:
            log_message(f"Startup connection attempt {attempt+1}/{startup_attempts}")
            
            # Try connecting with a longer timeout on startup
            await handle_h5075_device(GOVEE_MAC_ADDRESS, GOVEE_DEVICE_NAME, 
                                     retry_attempts=2, retry_interval=3)
            
            startup_connected = True
            log_message("Successfully connected to Bluetooth device on startup")
            break
        except Exception as e:
            log_message(f"Startup connection attempt {attempt+1} failed: {str(e)}")
            
            # Save offline status if needed
            if attempt == 0:  # Only save offline status on first failure
                await save_sensor_offline_status(GOVEE_DEVICE_NAME)
                log_message(f"Marked sensor {GOVEE_DEVICE_NAME} as offline")
            
            # Wait a bit longer between startup attempts
            if attempt < startup_attempts - 1:
                wait_time = 5 + (attempt * 5)  # Progressive backoff: 5, 10, 15, 20 seconds
                log_message(f"Waiting {wait_time} seconds before next startup attempt...")
                await asyncio.sleep(wait_time)
    
    if not startup_connected:
        log_message(f"WARNING: Failed to connect to Bluetooth device after {startup_attempts} startup attempts")
    
    while True:
        try:
            log_message("Starting regular sensor update")
            
            # Try to connect directly to the known Govee H5075 device
            try:
                log_message(f"Connecting to Govee H5075 at {GOVEE_MAC_ADDRESS}")
                
                # Standard connection with 3 retry attempts during normal operation
                await handle_h5075_device(GOVEE_MAC_ADDRESS, GOVEE_DEVICE_NAME)
                
                log_message("Govee H5075 update completed")
            except Exception as e:
                log_message(f"Error connecting to Govee H5075: {str(e)}")
                # Just mark the device as offline but don't propagate the error
                try:
                    await save_sensor_offline_status(GOVEE_DEVICE_NAME)
                    log_message(f"Marked sensor {GOVEE_DEVICE_NAME} as offline due to connection error")
                except Exception as offline_err:
                    log_message(f"Failed to mark sensor as offline: {offline_err}")
            
        except Exception as e:
            print(f"Error in update loop: {e}")
            log_message(f"Update loop error: {e}")
            # Add a small delay to prevent tight error loops
            await asyncio.sleep(5)
        
        # Wait before next update
        log_message("Waiting 5 minutes before next update...")
        await asyncio.sleep(300)  # 5 minutes

# For direct execution of this script
if __name__ == "__main__":
    # Run the updater directly when the script is executed
    update_sensor_data() 