#!/usr/bin/env python
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govee_control.settings')
django.setup()

# Import after Django setup
from garage.models import DeviceSettings

def show_settings():
    """Show all device settings in the database"""
    settings = DeviceSettings.objects.all()
    
    if not settings:
        print("No device settings found in the database.")
        return
    
    print(f"Found {settings.count()} device settings:")
    for setting in settings:
        print("\n" + "="*50)
        print(f"Device ID: {setting.device_id}")
        print("-"*50)
        print(f"Temperature Control:")
        print(f"  Enabled: {setting.temp_control_enabled}")
        print(f"  Source: {setting.temp_source}")
        print(f"  Target: {setting.target_temp}°C")
        print(f"  Function: {setting.temp_function}")
        print(f"Humidity Control:")
        print(f"  Enabled: {setting.humidity_control_enabled}")
        print(f"  Source: {setting.humidity_source}")
        print(f"  Target: {setting.target_humidity}%")
        print(f"  Function: {setting.humidity_function}")
        print(f"Last Updated: {setting.last_updated}")
        print("="*50)

if __name__ == "__main__":
    show_settings() 