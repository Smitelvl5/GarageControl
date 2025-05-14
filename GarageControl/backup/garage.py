import requests
import time
import json
from typing import Dict, Optional, List

class GoveeController:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openapi.api.govee.com/router/api/v1"
        self.headers = {
            "Govee-API-Key": api_key,
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_devices(self) -> Optional[List[Dict]]:
        """Get all devices from Govee API"""
        url = f"{self.base_url}/user/devices"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 200:
                return data.get("data", [])
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting devices: {e}")
            return None
        
    def get_device_state(self, device: str, model: str) -> Optional[Dict]:
        """Get the current state of a Govee device"""
        url = f"{self.base_url}/device/state"
        payload = {
            "device": device,
            "model": model
        }
        
        try:
            response = self.session.get(url, json=payload)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 200:
                return data.get("data")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting device state: {e}")
            return None

    def control_device(self, device: str, model: str, power_state: str) -> bool:
        """Control the power state of a Govee device"""
        url = f"{self.base_url}/device/control"
        payload = {
            "device": device,
            "model": model,
            "cmd": {
                "name": "turn",
                "value": power_state
            }
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("code") == 200
        except requests.exceptions.RequestException as e:
            print(f"Error controlling device: {e}")
            return False 