from django.db import models

class SensorData(models.Model):
    device_name = models.CharField(max_length=100, blank=True, null=True)
    temperature = models.FloatField(null=True)  # Temperature in Celsius, allow NULL for offline sensors
    humidity = models.FloatField(null=True)  # Allow NULL for offline sensors
    battery = models.IntegerField(default=0, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="online")  # 'online' or 'offline'
    # Additional sensor data fields
    dew_point = models.FloatField(null=True)  # Dew point in Celsius
    abs_humidity = models.FloatField(null=True)  # Absolute humidity in g/m³
    steam_pressure = models.FloatField(null=True)  # Steam pressure in mbar

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        status_indicator = " (OFFLINE)" if self.status == "offline" else ""
        if self.temperature is None or self.humidity is None:
            return f"{self.timestamp}: N/A{status_indicator}"
        return f"{self.timestamp}: {self.temperature}°C, {self.humidity}%{status_indicator}"

class DeviceSettings(models.Model):
    device_id = models.CharField(max_length=100, primary_key=True)
    
    # Temperature control settings
    temp_control_enabled = models.BooleanField(default=False)
    temp_source = models.CharField(max_length=10, default='inside')
    target_temp = models.FloatField(default=25.0) # Min temp in Celsius
    target_temp_max_celsius = models.FloatField(default=30.0) # Max temp in Celsius
    temp_function = models.CharField(max_length=10, default='above')
    
    # Humidity control settings
    humidity_control_enabled = models.BooleanField(default=False)
    humidity_source = models.CharField(max_length=10, default='inside')
    target_humidity = models.FloatField(default=50.0) # Min humidity %
    target_humidity_max = models.FloatField(default=60.0) # Max humidity %
    humidity_function = models.CharField(max_length=10, default='below')
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Settings for {self.device_id}" 