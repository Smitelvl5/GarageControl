from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('sensor-data/', views.sensor_data, name='sensor_data'),
    path('api/last-24h/', views.last_24h_data, name='last_24h_data'),
    path('control_device/', views.control_device, name='control_device'),
    path('get_device_status/', views.get_device_status, name='get_device_status'),
    path('get_devices/', views.get_devices, name='get_devices'),
    path('save_device_settings/', views.save_device_settings, name='save_device_settings'),
    path('get_device_settings/', views.get_device_settings, name='get_device_settings'),
    path('get_outdoor_data/', views.get_outdoor_data, name='get_outdoor_data'),
    path('refresh_bluetooth/', views.refresh_bluetooth_connection, name='refresh_bluetooth'),
] 