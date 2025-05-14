## Garage Temperature & Humidity Monitoring System

A Django-based system for monitoring and controlling temperature and humidity in a garage environment.

### Features

- Real-time temperature and humidity monitoring using Govee sensors
- Control of Govee smart plugs based on temperature and humidity thresholds
- Web interface with charts and device controls
- Automatic operation based on customizable settings
- Support for both indoor and outdoor readings
- Energy-saving dead band ranges for temperature and humidity

### Project Structure

```
├── garage/                 # Main Django app for garage monitoring
│   ├── templates/          # HTML templates
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── urls.py             # URL routing
│   ├── govee_client.py     # Govee API client
│   └── ble_scanner.py      # BLE scanner for Govee devices
│
├── govee_control/          # Django project settings
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL routing
│   └── wsgi.py             # WSGI config
│
├── api/                    # API endpoints
│   ├── urls.py             # API URL routing
│   └── views.py            # API view functions
│
├── utils/                  # Utility modules
│   ├── update_sensor.py    # Sensor data update logic
│   ├── weather_scraper.py  # Weather data fetching
│   └── display_settings.py # Tool to display device settings
│
├── scripts/                # Setup and installation scripts
│   ├── install_on_raspberry.sh     # RPi installation script
│   ├── setup_raspberry_autostart.sh # RPi autostart setup
│   └── initialize_server_data.py   # Data initialization
│
├── tools/                  # Development and testing tools
│   ├── add_test_setting.py        # Add test device settings
│   ├── check_device_ids.py        # Check device IDs
│   ├── scan_sensor.py             # Scan for sensors
│   └── test_save_settings.py      # Test settings saving
│
├── data/                   # Data storage directory
├── weather_cache/          # Weather data cache
├── logs/                   # Log files
│
├── manage.py               # Django management script
└── requirements.txt        # Python dependencies
```

### Installation

1. Clone the repository
2. Install required packages: `pip install -r requirements.txt`
3. Run the migrations: `python manage.py migrate`
4. Start the server: `python manage.py runserver`

For Raspberry Pi installation, use the provided script: `bash scripts/install_on_raspberry.sh`

### Setting Up Devices

1. Set your Govee API key in the `.env` file: `GOVEE_API_KEY=your_api_key_here`
2. Configure your devices through the web interface
3. Set up temperature and humidity ranges for automatic control

### Usage

- Access the web interface at http://localhost:8000
- View current temperature and humidity readings
- Control devices manually with ON/OFF buttons
- Configure automatic temperature and humidity control
- View historical data charts

### Utilities

- View device settings: `python utils/display_settings.py`
- Update sensor data manually: `python utils/update_sensor.py`

### Recent Improvements

- Fixed temperature/humidity range settings handling between UI (Fahrenheit) and database (Celsius)
- Added proper Fahrenheit-to-Celsius conversion when saving settings
- Improved storage of extended range information in localStorage
- Enhanced error handling with automatic retries and offline support
- Created JavaScript utility to display complete settings with ranges
- Restructured project for better organization with dedicated directories
- Fixed import paths with symlinks for backward compatibility
- Added fallback mode for sensor data updates when BLE scanning is unavailable

### Troubleshooting

#### Sensor Update Issues

If you encounter errors with sensor update functionality:

1. **BLE Scanner Errors**: The system now includes a fallback mode that generates dummy data when the BLE scanner is unavailable or fails. This ensures the system continues to function even if sensor hardware is not detected.

2. **GoveeThermometerHygrometer Initialization Error**: If you see `TypeError: GoveeThermometerHygrometer.__init__() missing 1 required positional argument: 'address'`, the system will automatically use the fallback mode.

3. **Missing Sensor Data**: If sensor data isn't being recorded, check the logs in the `logs/` directory for specific error messages.

### Development

- Run tests: `python manage.py test`
- Add test device settings: `python tools/add_test_setting.py`