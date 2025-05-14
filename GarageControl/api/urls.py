from django.urls import path
from . import views
from garage import views as garage_views

urlpatterns = [
    path('last-24h/', views.last_24h_data, name='last_24h_data'),
    path('sensor-data/', garage_views.sensor_data, name='sensor_data'),
]
