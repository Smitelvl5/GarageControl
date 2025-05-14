#!/usr/bin/env python
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govee_control.settings')
django.setup()

# Import after Django setup
from garage.models import DeviceSettings

def add_test_setting():
    """Add a test setting to the database"""
    # Use a test device ID
    device_id = "TEST_DEVICE"
    
    # Create or update settings for this device
    settings, created = DeviceSettings.objects.get_or_create(device_id=device_id)
    
    # Update with test values
    settings.temp_control_enabled = True
    settings.temp_source = 'inside'
    settings.target_temp = 23.5
    settings.temp_function = 'below'
    
    settings.humidity_control_enabled = True
    settings.humidity_source = 'inside'
    settings.target_humidity = 55.0
    settings.humidity_function = 'above'
    
    # Save the settings
    settings.save()
    
    action = "Created" if created else "Updated"
    print(f"{action} test settings for device {device_id}")
    
    # Print the settings to verify
    print("\n" + "="*50)
    print(f"Device ID: {settings.device_id}")
    print("-"*50)
    print(f"Temperature Control:")
    print(f"  Enabled: {settings.temp_control_enabled}")
    print(f"  Source: {settings.temp_source}")
    print(f"  Target: {settings.target_temp}°C")
    print(f"  Function: {settings.temp_function}")
    print(f"Humidity Control:")
    print(f"  Enabled: {settings.humidity_control_enabled}")
    print(f"  Source: {settings.humidity_source}")
    print(f"  Target: {settings.target_humidity}%")
    print(f"  Function: {settings.humidity_function}")
    print(f"Last Updated: {settings.last_updated}")
    print("="*50)

if __name__ == "__main__":
    add_test_setting() 