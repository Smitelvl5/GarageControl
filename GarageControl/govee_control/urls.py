from django.contrib import admin
from django.urls import path, include
from garage import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Explicitly include critical endpoints at root level
    path('get_device_status/', views.get_device_status, name='get_device_status'),
    path('control_device/', views.control_device, name='control_device'),
    path('api/last-24h/', views.last_24h_data, name='last_24h_data'),
    path('api/sensor_data/', views.sensor_data, name='sensor_data'),
    # Settings endpoints
    path('save_device_settings/', views.save_device_settings, name='save_device_settings'),
    path('get_device_settings/', views.get_device_settings, name='get_device_settings'),
    # Add outdoor temperature endpoint
    path('get_outdoor_data/', views.get_outdoor_data, name='get_outdoor_data'),
    # Use api without a prefix for root level API access, ensuring it's compatible with the frontend
    path('', views.index, name='index'),
    path('api/', include('api.urls')),
    # path('sensor_dashboard/', include('sensor_dashboard.urls')),
    path('garage/', include('garage.urls')),
] 