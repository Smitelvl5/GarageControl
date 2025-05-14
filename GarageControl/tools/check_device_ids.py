#!/usr/bin/env python
import os
import sys
import django
import json
import requests

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govee_control.settings')
django.setup()

# Import after Django setup
from garage.models import DeviceSettings
from garage.govee_client import GoveeClient

def check_device_ids():
    """Compare device IDs in the database with actual device IDs from the API"""
    # Show all settings in the database
    settings = DeviceSettings.objects.all()
    
    db_device_ids = [setting.device_id for setting in settings]
    print(f"Device IDs in database ({len(db_device_ids)}):")
    for device_id in db_device_ids:
        print(f"  - {device_id}")
    
    # Get actual device IDs from Govee API
    print("\nFetching actual device IDs from Govee API...")
    client = GoveeClient()
    devices = client.get_devices()
    
    api_device_ids = [device['device'] for device in devices if 'device' in device]
    print(f"Device IDs from API ({len(api_device_ids)}):")
    for device_id in api_device_ids:
        print(f"  - {device_id}")
    
    # Compare IDs
    print("\nComparison:")
    for api_id in api_device_ids:
        if api_id in db_device_ids:
            print(f"  ✓ {api_id} - Found in both database and API")
        else:
            print(f"  ✗ {api_id} - Only in API, not in database")
    
    for db_id in db_device_ids:
        if db_id not in api_device_ids:
            print(f"  ! {db_id} - Only in database, not in API")
    
    # Additional test - try loading settings via the API endpoint
    print("\nTesting API endpoint for first actual device...")
    if api_device_ids:
        test_device_id = api_device_ids[0]
        try:
            response = requests.get(f"http://127.0.0.1:8000/get_device_settings/?device_id={test_device_id}")
            print(f"API response status: {response.status_code}")
            data = response.json()
            print(f"Settings for {test_device_id}: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"Error testing API endpoint: {e}")

if __name__ == "__main__":
    check_device_ids() 