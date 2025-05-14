#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path

# Calculate the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

def celsius_to_fahrenheit(celsius):
    if celsius is None:
        return None
    return (celsius * 9/5) + 32

def get_table_names(cursor):
    """Get all table names from the database"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]

def main():
    # Get the database file path
    db_path = os.path.join(BASE_DIR, 'db.sqlite3')
    
    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        return
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First, list all available tables to help diagnose issues
        tables = get_table_names(cursor)
        print(f"Available tables in database: {', '.join(tables)}")
        
        # Use the garage_devicesettings table that was detected
        settings_table = 'garage_devicesettings'
        
        # Check if the table exists
        if settings_table not in tables:
            print(f"\nError: Table '{settings_table}' not found in database.")
            # Show possible alternatives
            device_tables = [t for t in tables if 'device' in t.lower() or 'settings' in t.lower() or 'govee' in t.lower()]
            if device_tables:
                print(f"Possible device settings tables found: {', '.join(device_tables)}")
                print("Please update the script with the correct table name.")
            else:
                print("No device settings tables found in the database.")
            return
        
        print(f"\nUsing table: {settings_table}\n")
        
        # Query the device settings table
        cursor.execute(f"SELECT * FROM {settings_table}")
        device_settings = cursor.fetchall()
        
        if not device_settings:
            print("No device settings found in the database.")
            return
        
        # Get column names from the first row
        if device_settings:
            columns = device_settings[0].keys()
            print(f"Columns in {settings_table}: {', '.join(columns)}")
        
        print(f"Found {len(device_settings)} device settings:\n")
        
        # Print each device's settings
        for settings in device_settings:
            device_id_field = 'device_id' if 'device_id' in settings.keys() else 'device'
            device_id = settings[device_id_field]
            
            print("=" * 50)
            print(f"Device ID: {device_id}")
            print("-" * 50)
            
            # Temperature control settings - adapt to available columns
            print("Temperature Control:")
            if 'temp_control_enabled' in settings.keys():
                print(f"  Enabled: {bool(settings['temp_control_enabled'])}")
            
            if 'temp_source' in settings.keys():
                print(f"  Source: {settings['temp_source']}")
            
            # Display temperature in both C and F if available
            if 'target_temp' in settings.keys():
                temp_c = settings['target_temp']
                temp_f = celsius_to_fahrenheit(temp_c)
                print(f"  Target: {temp_c}°C ({temp_f:.1f}°F)")
            
            # Function (above/below)
            temp_function = settings['temp_function'] if 'temp_function' in settings.keys() else None
            if temp_function:
                print(f"  Function: {temp_function}")
            
            # Humidity control settings
            print("Humidity Control:")
            if 'humidity_control_enabled' in settings.keys():
                print(f"  Enabled: {bool(settings['humidity_control_enabled'])}")
            
            if 'humidity_source' in settings.keys():
                print(f"  Source: {settings['humidity_source']}")
            
            if 'target_humidity' in settings.keys():
                print(f"  Target: {settings['target_humidity']}%")
            
            if 'humidity_function' in settings.keys():
                print(f"  Function: {settings['humidity_function']}")
            
            # Show last updated if available
            if 'updated_at' in settings.keys():
                last_updated = settings['updated_at']
                print(f"Last Updated: {last_updated}")
            
            # Explain the settings in a more user-friendly way if we have enough information
            if temp_function and 'target_temp' in settings.keys() and 'humidity_function' in settings.keys() and 'target_humidity' in settings.keys():
                print("\nTranslated Settings:")
                
                # Temperature range explanation
                temp_enabled = bool(settings['temp_control_enabled']) if 'temp_control_enabled' in settings.keys() else False
                if temp_enabled:
                    temp_range_type = "inside" if temp_function == "above" else "outside"
                    temp_min = temp_f  # Use the Fahrenheit value for display
                    temp_max = temp_min + 10.0  # Estimated max based on defaults
                    
                    if temp_range_type == "inside":
                        print(f"  Temperature: Turn ON when between {temp_min:.1f}°F and {temp_max:.1f}°F")
                    else:
                        print(f"  Temperature: Turn ON when below {temp_min:.1f}°F or above {temp_max:.1f}°F")
                else:
                    print("  Temperature control is disabled")
                    
                # Humidity range explanation
                humidity_enabled = bool(settings['humidity_control_enabled']) if 'humidity_control_enabled' in settings.keys() else False
                if humidity_enabled:
                    humidity_function = settings['humidity_function']
                    humidity_range_type = "inside" if humidity_function == "above" else "outside"
                    humidity_min = settings['target_humidity']
                    humidity_max = humidity_min + 20.0  # Estimated max based on defaults
                    
                    if humidity_range_type == "inside":
                        print(f"  Humidity: Turn ON when between {humidity_min}% and {humidity_max}%")
                    else:
                        print(f"  Humidity: Turn ON when below {humidity_min}% or above {humidity_max}%")
                else:
                    print("  Humidity control is disabled")
            
            print("=" * 50)
            print()
    
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        print("\nDatabase details:")
        try:
            if 'cursor' in locals() and 'conn' in locals():
                tables = get_table_names(cursor)
                print(f"Tables in database: {', '.join(tables)}")
                
                # Try to examine schema of the first table
                if tables:
                    cursor.execute(f"PRAGMA table_info({tables[0]})")
                    columns = cursor.fetchall()
                    print(f"\nSchema of table {tables[0]}:")
                    for col in columns:
                        print(f"  {col[1]} ({col[2]})")
        except:
            print("Could not retrieve additional database information")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 