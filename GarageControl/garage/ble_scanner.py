import asyncio
# from bleak import BleakScanner
from .models import SensorData
import logging
# import struct
from govee_h5075.govee_h5075 import Measurement, GoveeThermometerHygrometer

# Set up logging
logger = logging.getLogger(__name__)

class GoveeScanner:
    def __init__(self):
        # self.scanner = BleakScanner()
        self.devices = {}

    def process_sensor_data(self, address: str, name: str, battery: int, measurement: Measurement):
        """
        Process data from a Govee sensor using the proper library callback
        
        This function matches the signature expected by GoveeThermometerHygrometer.scan()
        """
        logger.info(f"Received data from Govee sensor: {name} ({address})")
        logger.info(f"  Temperature: {measurement.temperatureC:.2f}°C / {measurement.temperatureF:.2f}°F")
        logger.info(f"  Humidity: {measurement.relHumidity:.2f}%")
        logger.info(f"  Battery: {battery}%")
        logger.info(f"  Dew Point: {measurement.dewPointC:.2f}°C")
        
        # Store the data in our devices dictionary
        self.devices[address] = {
            'name': name,
            'temperature': round(measurement.temperatureC, 2),
            'humidity': round(measurement.relHumidity, 2),
            'battery': battery,
            'dew_point': round(measurement.dewPointC, 2),
            'abs_humidity': round(measurement.absHumidity, 2)
        }

    # Add the scan method for compatibility with older code
    async def scan(self, timeout=10):
        """For backwards compatibility"""
        return await self.start_scanning(timeout)

    async def start_scanning(self, timeout=10):
        """
        Start scanning for BLE devices for a specified duration
        
        Args:
            timeout (int): Scan duration in seconds
            
        Returns:
            dict: Dictionary of found devices with address as key
        """
        logger.info(f"Starting BLE scan for {timeout} seconds...")
        self.devices = {}  # Reset devices dictionary
        
        try:
            # Use the GoveeThermometerHygrometer.scan method directly
            # This will properly decode the manufacturer data using the library
            await GoveeThermometerHygrometer.scan(
                consumer=self.process_sensor_data,  # Use our callback that matches the expected signature
                duration=timeout,                   # Use the specified timeout
                progress=lambda found: logger.debug(f"Scanning... {found} Bluetooth devices found")
            )
            
            # Log results
            devices_with_temp = [addr for addr, data in self.devices.items() 
                                if data.get('temperature') is not None]
            logger.info(f"Scan complete. Found {len(self.devices)} devices, {len(devices_with_temp)} with temperature data")
            
            # Log each device with temperature data
            for addr in devices_with_temp:
                data = self.devices[addr]
                logger.info(f"Device with data: {data['name']} - Temp: {data['temperature']}°C, Humidity: {data['humidity']}%")
                
            return self.devices
        except Exception as e:
            logger.error(f"Error in BLE scanning: {str(e)}")
            return {}

    def get_device_data(self, address):
        return self.devices.get(address) 