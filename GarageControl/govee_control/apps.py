from django.apps import AppConfig
import asyncio
import threading
import os
import sys

class GoveeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'govee_control'

    def ready(self):
        print("--- GoveeConfig.ready() method CALLED ---")
        # Avoid running twice in development server
        # Only run in the worker process (not in the main autoreload process)
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
            
        # Import and run sensor update job
        print("GoveeConfig.ready() method executing past RUN_MAIN check.")

        if not asyncio.get_event_loop().is_running():
            try:
                from utils.update_sensor import update_sensor_data
                print("Starting sensor update thread...")
                update_thread = threading.Thread(target=update_sensor_data)
                update_thread.daemon = True
                update_thread.start()
            except Exception as e:
                print(f"Error starting sensor update thread: {str(e)}")
                print("Django server will continue running without sensor updates") 