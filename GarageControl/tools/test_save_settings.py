#!/usr/bin/env python
import requests
import json

def test_save_endpoint():
    """Test saving device settings via the API endpoint directly"""
    # Test data
    test_settings = {
        'device_id': 'API_TEST_DEVICE',
        'temp_control_enabled': True,
        'temp_source': 'inside',
        'target_temp': 24.0,
        'temp_function': 'above',
        'humidity_control_enabled': True,
        'humidity_source': 'inside',
        'target_humidity': 60.0,
        'humidity_function': 'below'
    }
    
    print("Sending test settings to save_device_settings endpoint...")
    
    # First try the FormData approach
    response = requests.post(
        'http://127.0.0.1:8000/save_device_settings/',
        data={'data': json.dumps(test_settings)}
    )
    
    print(f"Response status code: {response.status_code}")
    try:
        print(f"Response content: {response.json()}")
        print("\nFormData approach result:", "SUCCESS" if response.status_code == 200 and response.json().get('success') else "FAILED")
    except:
        print(f"Could not parse response as JSON: {response.text}")
        print("\nFormData approach result: FAILED")
    
    # Wait a bit
    print("\n" + "-" * 50 + "\n")
    
    # Now try the direct JSON approach
    response = requests.post(
        'http://127.0.0.1:8000/save_device_settings/',
        json=test_settings
    )
    
    print(f"Response status code: {response.status_code}")
    try:
        print(f"Response content: {response.json()}")
        print("\nDirect JSON approach result:", "SUCCESS" if response.status_code == 200 and response.json().get('success') else "FAILED")
    except:
        print(f"Could not parse response as JSON: {response.text}")
        print("\nDirect JSON approach result: FAILED")

if __name__ == "__main__":
    test_save_endpoint() 