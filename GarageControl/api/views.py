from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.utils import timezone
from garage.models import SensorData

@csrf_exempt
def last_24h_data(request):
    """API endpoint to get last 24 hours of sensor data"""
    day_ago = timezone.now() - timedelta(hours=24)
    readings = SensorData.objects.filter(timestamp__gte=day_ago).order_by('timestamp')
    
    if not readings.exists():
        return JsonResponse({'readings': []})
        
    data = [
        {
            'timestamp': timezone.localtime(reading.timestamp).strftime('%Y-%m-%d %I:%M:%S %p'),
            'temperature': reading.temperature,
            'humidity': reading.humidity,
        }
        for reading in readings
    ]
    return JsonResponse({'readings': data})
