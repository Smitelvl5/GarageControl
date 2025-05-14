from django.shortcuts import render
from django.http import JsonResponse
from .models import SensorData, DeviceSettings
from datetime import datetime, timedelta
from django.utils import timezone
from .govee_client import GoveeClient
from .ble_scanner import GoveeScanner
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import time
import os

# First, remove the incorrect import that may be causing issues
# Import the weather scraper module correctly
try:
    from utils.weather_scraper import get_latest_outdoor_temperature
    HAS_WEATHER_SCRAPER = True
    print("Weather scraper module loaded successfully")
except ImportError as e:
    HAS_WEATHER_SCRAPER = False
    print(f"Weather scraper module not available - outdoor temperature feature disabled. Error: {e}")

# Station ID for Weather Underground
WEATHER_STATION_ID = os.getenv('STATION', 'KTNMEMPH176')  # Get station ID from .env file

# Cache for outdoor temperature data
_outdoor_temp_cache = {
    'data': None,
    'last_updated': 0,
    'update_interval': 900  # 15 minutes in seconds
}

# Cache for storing devices
_device_cache = {
    'devices': None,
    'last_updated': 0,
    'update_interval': 1800  # 30 minutes in seconds (was 300 seconds = 5 minutes)
}

# Utility function to convert Celsius to Fahrenheit
def celsius_to_fahrenheit(celsius):
    """
    Convert temperature from Celsius to Fahrenheit
    
    Args:
        celsius (float): Temperature in Celsius
        
    Returns:
        float: Temperature in Fahrenheit
    """
    if celsius is None:
        return None
    return (celsius * 9/5) + 32

def get_cached_devices():
    """Get devices from cache or fetch new ones if cache is expired"""
    current_time = time.time()
    if (_device_cache['devices'] is None or 
            current_time - _device_cache['last_updated'] > _device_cache['update_interval']):
        # Cache expired or not initialized, fetch new devices
        print("Fetching fresh device data from API...")
        client = GoveeClient()
        try:
            devices = client.get_devices()
            if devices:
                print(f"Cached {len(devices)} devices from Govee API")
                _device_cache['devices'] = devices
                _device_cache['last_updated'] = current_time
            else:
                print("No devices returned from API")
        except Exception as e:
            print(f"Error fetching devices: {str(e)}")
            # Keep old cache if available
            if _device_cache['devices'] is None:
                _device_cache['devices'] = []
    else:
        print("Using cached device data")
    
    return _device_cache['devices']

def index(request):
    # Get the latest sensor reading
    latest = SensorData.objects.first()
    
    # Get readings from the last 24 hours
    day_ago = timezone.now() - timedelta(hours=24)
    recent_readings = SensorData.objects.filter(timestamp__gte=day_ago)
    
    # Get Govee API key status
    client = GoveeClient()
    api_key = client.api_key
    if api_key:
        print(f"Using API key: {api_key[:4]}...{api_key[-4:]}")
    else:
        print("WARNING: No API key found!")
    
    # Get devices from cache
    devices = get_cached_devices()
    
    # Convert to JSON for template
    devices_json = json.dumps(devices)
    
    context = {
        'latest': latest,
        'recent_readings': recent_readings,
        'devices': devices,
        'devices_json': devices_json
    }
    
    return render(request, 'garage/index.html', context)

def sensor_data(request):
    # Get the latest sensor reading
    latest = SensorData.objects.first()
    
    if latest:
        print(f"Latest sensor reading: {latest} - Status: {latest.status}")
        # For offline sensors or NULL values, return NULL values in the API response
        if latest.status == "offline" or latest.temperature is None or latest.humidity is None:
            data = {
                'temperature': None,
                'humidity': None,
                'timestamp': timezone.localtime(latest.timestamp).strftime('%Y-%m-%d %I:%M:%S %p'),
                'status': 'offline',
                'battery': latest.battery,
                'dew_point': None,
                'abs_humidity': None,
                'steam_pressure': None,
                'dew_point_f': None
            }
            print(f"Returning OFFLINE sensor data: {data}")
        else:
            data = {
                'temperature': latest.temperature,
                'humidity': latest.humidity,
                'timestamp': timezone.localtime(latest.timestamp).strftime('%Y-%m-%d %I:%M:%S %p'),
                'status': 'online',
                'battery': latest.battery,
                'dew_point': latest.dew_point,
                'abs_humidity': latest.abs_humidity,
                'steam_pressure': latest.steam_pressure,
                'dew_point_f': celsius_to_fahrenheit(latest.dew_point)
            }
            print(f"Returning ONLINE sensor data: {data}")
    else:
        data = {
            'temperature': None,
            'humidity': None,
            'timestamp': None,
            'status': 'offline',  # Changed from 'unknown' to 'offline' to ensure N/A is displayed
            'battery': None,
            'dew_point': None,
            'abs_humidity': None,
            'steam_pressure': None,
            'dew_point_f': None
        }
        print("No sensor data found, returning offline status")
    
    return JsonResponse(data)

def last_24h_data(request):
    day_ago = timezone.now() - timedelta(hours=24)
    readings = SensorData.objects.filter(timestamp__gte=day_ago).order_by('timestamp')
    data = []
    for reading in readings:
        # Handle NULL values by creating safe entry with None values
        # which will be displayed as N/A in the frontend
        if reading.status == "offline" or reading.temperature is None or reading.humidity is None:
            entry = {
                'timestamp': timezone.localtime(reading.timestamp).strftime('%Y-%m-%d %I:%M:%S %p'),
                'temperature': None,
                'temperature_f': None,
                'humidity': None,
                'status': reading.status
            }
        else:
            # For normal readings with data
            entry = {
                'timestamp': timezone.localtime(reading.timestamp).strftime('%Y-%m-%d %I:%M:%S %p'),
                'temperature': reading.temperature,  # Temperature in Celsius
                'temperature_f': celsius_to_fahrenheit(reading.temperature),  # Temperature in Fahrenheit
                'humidity': reading.humidity,
                'status': reading.status
            }
        data.append(entry)
            
    return JsonResponse({'readings': data})

@csrf_exempt
def control_device(request):
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        model = request.POST.get('model', 'H5080')
        action = request.POST.get('action')
        
        if not device_id:
            return JsonResponse({'success': False, 'error': 'Device ID is required'}, status=400)
        
        client = GoveeClient()
        
        try:
            result = False
            error_msg = ''
            
            if action == 'on':
                print(f"Turning ON device {device_id}")
                result = client.turn_on(device_id, model)
                if not result:
                    error_msg = "Failed to turn on device"
            elif action == 'off':
                print(f"Turning OFF device {device_id}")
                result = client.turn_off(device_id, model)
                if not result:
                    error_msg = "Failed to turn off device"
            else:
                error_msg = 'Invalid action for smart plug. Only on/off actions are supported.'
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            
            if result:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': error_msg}, status=500)
        except Exception as e:
            error_msg = f"Error controlling device: {str(e)}"
            print(error_msg)
            return JsonResponse({'success': False, 'error': error_msg}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

def get_device_status(request):
    device_id = request.GET.get('device_id')
    model = request.GET.get('model', 'H5080')
    
    if not device_id:
        return JsonResponse({'success': False, 'error': 'Device ID is required'}, status=400)
    
    # Special case for test parameter
    if device_id.lower() == 'test':
        print("Test device requested, returning mock data")
        return JsonResponse({
            'success': True,
            'power': False,
            'brightness': 100,
            'color': None,
            'model': model,
            'device_id': device_id,
            'is_test': True
        })
    
    print(f"Fetching status for device {device_id} (model: {model})")
    
    try:
        # Create Govee client
        client = GoveeClient()
        
        # Get device state from Govee API
        device_state = client.get_device_state(device_id, model)
        
        if device_state:
            print(f"Successfully got device state: {device_state}")
            return JsonResponse({
                'success': True,
                'power': device_state.get('powerState'),
                'brightness': device_state.get('brightness'),
                'color': device_state.get('color'),
                'model': model,
                'device_id': device_id
            })
        else:
            # Return a more graceful error for failed API requests
            error_msg = 'Failed to get device state from Govee API'
            print(error_msg)
            return JsonResponse({
                'success': False, 
                'error': error_msg,
                'power': False,  # Default state for UI
                'device_id': device_id,
                'model': model
            }, status=200)  # Return 200 instead of 404 for better UI handling
    except ValueError as e:
        # This is likely due to missing API key
        error_msg = f"API key error: {str(e)}"
        print(error_msg)
        return JsonResponse({
            'success': False, 
            'error': error_msg,
            'power': False,
            'device_id': device_id,
            'model': model
        }, status=200)
    except Exception as e:
        error_msg = f"Error getting device status: {str(e)}"
        print(error_msg)
        return JsonResponse({
            'success': False, 
            'error': error_msg,
            'power': False,
            'device_id': device_id,
            'model': model
        }, status=200)  # Return 200 instead of 500 for better UI handling

@csrf_exempt
def save_device_settings(request):
    if request.method == 'POST':
        try:
            # Handle both FormData or direct JSON
            if 'data' in request.POST:
                # FormData approach
                data = json.loads(request.POST.get('data'))
            else:
                # Direct JSON approach (fallback)
                try:
                    data = json.loads(request.body)
                except:
                    # If that fails, check if any POST data exists
                    if request.POST:
                        data = request.POST.dict()
                    else:
                        return JsonResponse({'success': False, 'error': 'No data received'}, status=400)
            
            device_id = data.get('device_id')
            print(f"Received settings for device {device_id}: {data}")
            
            if not device_id:
                return JsonResponse({'success': False, 'error': 'Device ID is required'}, status=400)
            
            # Get or create settings for this device
            settings, created = DeviceSettings.objects.get_or_create(device_id=device_id)
            
            # Update temperature settings
            settings.temp_control_enabled = data.get('temp_control_enabled', settings.temp_control_enabled)
            settings.temp_source = data.get('temp_source', settings.temp_source)
            settings.target_temp = data.get('target_temp', settings.target_temp)
            settings.target_temp_max_celsius = data.get('target_temp_max_celsius', settings.target_temp_max_celsius)
            settings.temp_function = data.get('temp_function', settings.temp_function)
            
            # Update humidity settings
            settings.humidity_control_enabled = data.get('humidity_control_enabled', settings.humidity_control_enabled)
            settings.humidity_source = data.get('humidity_source', settings.humidity_source)
            settings.target_humidity = data.get('target_humidity', settings.target_humidity)
            settings.target_humidity_max = data.get('target_humidity_max', settings.target_humidity_max)
            settings.humidity_function = data.get('humidity_function', settings.humidity_function)
            
            settings.save()
            
            # Print settings to server log for debugging
            print(f"SETTINGS SAVED for device {device_id}:")
            print(f"  Temperature: enabled={settings.temp_control_enabled}, source={settings.temp_source}, target_min_c={settings.target_temp}, target_max_c={settings.target_temp_max_celsius}, function={settings.temp_function}")
            print(f"  Humidity: enabled={settings.humidity_control_enabled}, source={settings.humidity_source}, target_min_pct={settings.target_humidity}, target_max_pct={settings.target_humidity_max}, function={settings.humidity_function}")
            
            return JsonResponse({
                'success': True,
                'message': 'Settings saved successfully'
            })
        except Exception as e:
            error_msg = f"Error saving device settings: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': error_msg}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

def get_device_settings(request):
    device_id = request.GET.get('device_id')
    force_refresh = request.GET.get('force_refresh', 'false').lower() == 'true'
    
    if not device_id:
        return JsonResponse({'success': False, 'error': 'Device ID is required'}, status=400)
    
    try:
        # If force_refresh is True, we want to query the database directly
        # rather than using any cached data
        settings = DeviceSettings.objects.filter(device_id=device_id).first()
        
        if settings:
            # Print settings to server log for debugging
            print(f"SETTINGS RETRIEVED for device {device_id}:")
            print(f"  Temperature: enabled={settings.temp_control_enabled}, source={settings.temp_source}, target_min_c={settings.target_temp}, target_max_c={settings.target_temp_max_celsius}, function={settings.temp_function}")
            print(f"  Humidity: enabled={settings.humidity_control_enabled}, source={settings.humidity_source}, target_min_pct={settings.target_humidity}, target_max_pct={settings.target_humidity_max}, function={settings.humidity_function}")
            
            # Ensure the response is not cached
            response = JsonResponse({
                'success': True,
                'settings': {
                    'temp_control_enabled': settings.temp_control_enabled,
                    'temp_source': settings.temp_source,
                    'target_temp': settings.target_temp,  # Min Temp in Celsius
                    'target_temp_max_celsius': settings.target_temp_max_celsius, # Max Temp in Celsius
                    'temp_function': settings.temp_function,
                    'humidity_control_enabled': settings.humidity_control_enabled,
                    'humidity_source': settings.humidity_source,
                    'target_humidity': settings.target_humidity, # Min Humidity %
                    'target_humidity_max': settings.target_humidity_max, # Max Humidity %
                    'humidity_function': settings.humidity_function
                }
            })
            # Add cache control headers
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        else:
            # Return default settings if none exist
            print(f"NO SETTINGS FOUND for device {device_id} - returning defaults")
            response = JsonResponse({
                'success': True,
                'settings': {
                    'temp_control_enabled': False,
                    'temp_source': 'inside',
                    'target_temp': 25.0, # Min Temp in Celsius
                    'target_temp_max_celsius': 30.0, # Max Temp in Celsius
                    'temp_function': 'above',
                    'humidity_control_enabled': False,
                    'humidity_source': 'inside',
                    'target_humidity': 50.0, # Min Humidity %
                    'target_humidity_max': 60.0, # Max Humidity %
                    'humidity_function': 'below'
                }
            })
            # Add cache control headers for defaults as well
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
    except Exception as e:
        error_msg = f"Error getting device settings: {str(e)}"
        print(error_msg)
        return JsonResponse({'success': False, 'error': error_msg}, status=500)

def get_devices(request):
    """Return the list of Govee devices as JSON."""
    client = GoveeClient()
    
    try:
        devices = client.get_devices()
        if not devices:
            devices = []
    except Exception as e:
        print(f"Error getting devices: {str(e)}")
        devices = []
    
    return JsonResponse({'devices': devices})

def get_outdoor_data(request):
    """Get outdoor temperature and humidity data from Weather Underground"""
    # Check if weather scraper is available
    if not HAS_WEATHER_SCRAPER:
        return JsonResponse({
            'success': False, 
            'error': 'Weather scraper module not available',
            'outdoor_temp': None,
            'outdoor_humidity': None,
            'status': 'error'
        })
    
    # Check if station ID is configured
    station_id = os.getenv('STATION', 'KTNMEMPH176')
    if not station_id:
        return JsonResponse({
            'success': False, 
            'error': 'No weather station ID configured. Set WEATHER_STATION_ID environment variable.',
            'outdoor_temp': None,
            'outdoor_humidity': None,
            'status': 'error'
        })
    
    # Check cache first
    current_time = time.time()
    if (_outdoor_temp_cache['data'] is not None and 
            current_time - _outdoor_temp_cache['last_updated'] < _outdoor_temp_cache['update_interval']):
        print("Using cached outdoor temperature data")
        data = _outdoor_temp_cache['data']
    else:
        # Fetch fresh data
        print("Fetching fresh outdoor temperature data")
        try:
            weather_data = get_latest_outdoor_temperature(station_id)
            
            if weather_data:
                print(f"Received weather data: {weather_data}")
                # The data is already in Fahrenheit from the Weather Underground API
                # We don't need to convert it
                temp_f = weather_data['temperature']
                    
                data = {
                    'temperature': weather_data['temperature'],  # Store the original value
                    'temperature_f': temp_f,  # This is already in Fahrenheit
                    'humidity': weather_data['humidity'],
                    'timestamp': weather_data['timestamp'],
                    'status': weather_data.get('status', 'unknown'),
                    # Add all other weather fields
                    'time': weather_data.get('time'),
                    'dew_point': weather_data.get('dew_point'),
                    'wind_direction': weather_data.get('wind_direction'),
                    'wind_speed': weather_data.get('wind_speed'),
                    'wind_gust': weather_data.get('wind_gust'),
                    'pressure': weather_data.get('pressure'),
                    'precip_rate': weather_data.get('precip_rate'),
                    'precip_accum': weather_data.get('precip_accum'),
                    'uv': weather_data.get('uv')
                }
                _outdoor_temp_cache['data'] = data
                _outdoor_temp_cache['last_updated'] = current_time
                
                print(f"Cached weather data: {data}")
            else:
                error_msg = "Weather data not available"
                print(error_msg)
                return JsonResponse({
                    'success': False, 
                    'error': error_msg,
                    'outdoor_temp': None,
                    'outdoor_humidity': None,
                    'status': 'error'
                })
        except Exception as e:
            error_msg = f"Error fetching outdoor temperature: {str(e)}"
            print(error_msg)
            return JsonResponse({
                'success': False, 
                'error': error_msg,
                'outdoor_temp': None,
                'outdoor_humidity': None,
                'status': 'error'
            })
    
    # Format the response
    response_data = {
        'success': True,
        'outdoor_temp': data.get('temperature_f'),  # This is already in Fahrenheit
        'outdoor_humidity': data.get('humidity'),
        'timestamp': data.get('timestamp'),
        'status': data.get('status', 'unknown'),
        # Include all the additional weather data
        'time': data.get('time'),
        'dew_point': data.get('dew_point'),
        'wind_direction': data.get('wind_direction'),
        'wind_speed': data.get('wind_speed'),
        'wind_gust': data.get('wind_gust'), 
        'pressure': data.get('pressure'),
        'precip_rate': data.get('precip_rate'),
        'precip_accum': data.get('precip_accum'),
        'uv': data.get('uv')
    }
    
    # Only claim success if we have temperature data or status is not error/offline
    if (data.get('temperature_f') is None and 
        data.get('status') in ['error', 'offline']):
        response_data['success'] = False
        response_data['error'] = f"Outdoor sensor is {data.get('status', 'unavailable')}"
    
    return JsonResponse(response_data)

@csrf_exempt
def refresh_bluetooth_connection(request):
    """
    API endpoint to manually refresh the Bluetooth connection
    This will attempt to reconnect to the Bluetooth device and get fresh data
    """
    import asyncio
    from utils.update_sensor import handle_h5075_device, GOVEE_MAC_ADDRESS, GOVEE_DEVICE_NAME, save_sensor_offline_status
    
    if request.method == 'POST':
        try:
            # Create new event loop for the async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            print("Manual refresh of Bluetooth connection requested")
            
            # First, explicitly force disconnect any existing connection
            async def force_disconnect_and_reconnect():
                from govee_h5075.govee_h5075 import GoveeThermometerHygrometer
                try:
                    print(f"Attempting to disconnect any existing connection to {GOVEE_MAC_ADDRESS}")
                    device = GoveeThermometerHygrometer(GOVEE_MAC_ADDRESS)
                    if hasattr(device, 'is_connected') and device.is_connected:
                        print("Existing connection found, disconnecting...")
                        await device.disconnect()
                        print("Disconnected successfully")
                    else:
                        print("No existing connection found")
                    
                    # Add a small delay before reconnecting
                    await asyncio.sleep(1)
                    
                    # Attempt reconnection with handle_h5075_device that has retry logic
                    print(f"Now attempting to reconnect to {GOVEE_MAC_ADDRESS}")
                    return await handle_h5075_device(GOVEE_MAC_ADDRESS, GOVEE_DEVICE_NAME)
                except Exception as e:
                    print(f"Error during disconnect/reconnect: {str(e)}")
                    # Still mark as offline in case of failure
                    await save_sensor_offline_status(GOVEE_DEVICE_NAME)
                    raise e
            
            # Execute our combined disconnect/reconnect function
            try:
                result = loop.run_until_complete(force_disconnect_and_reconnect())
                print("Manual Bluetooth connection refresh completed successfully")
                
                # Get the latest data
                latest = SensorData.objects.first()
                if latest and latest.status == "online":
                    status = "success"
                    message = "Successfully connected to sensor"
                else:
                    status = "error"
                    message = "Connected but couldn't get valid readings"
            except Exception as e:
                print(f"Error in manual Bluetooth refresh: {str(e)}")
                loop.run_until_complete(save_sensor_offline_status(GOVEE_DEVICE_NAME))
                status = "error"
                message = f"Error connecting to sensor: {str(e)}"
            finally:
                loop.close()
                
            return JsonResponse({
                'status': status,
                'message': message
            })
        except Exception as e:
            print(f"Exception in refresh_bluetooth_connection: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f"Server error: {str(e)}"
            })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Only POST requests are allowed'
        }) 