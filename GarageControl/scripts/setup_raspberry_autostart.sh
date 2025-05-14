#!/bin/bash
# Setup Script for Raspberry Pi Autostart
# This script configures the Django server to start automatically when the Raspberry Pi boots

# Change to the directory containing the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Get the parent directory (project root)
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SCRIPT_DIR"

# Create a systemd service file
SERVICE_FILE="/etc/systemd/system/django-server.service"

# Define the service file content
SERVICE_CONTENT="[Unit]
Description=Django Server with Sensor Integration
After=network.target bluetooth.target bluetooth.service
Wants=bluetooth.target bluetooth.service
# Ensure network and Bluetooth are fully loaded before starting
Requires=network-online.target
After=network-online.target

[Service]
# Add a delay to ensure Bluetooth has fully initialized
ExecStartPre=/bin/sleep 20
ExecStart=/home/GarageControl/venv/bin/python $PROJECT_DIR/manage.py runserver 0.0.0.0:8000
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=$PROJECT_DIR
Restart=always
RestartSec=10
# Environment variables
EnvironmentFile=$PROJECT_DIR/.env
# Add Bluetooth capabilities
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW

[Install]
WantedBy=multi-user.target
"

# We need sudo to write to /etc/systemd/system/
echo "Creating systemd service file... (requires sudo)"
echo "$SERVICE_CONTENT" | sudo tee $SERVICE_FILE > /dev/null

# Check if service file was created successfully
if [ $? -eq 0 ]; then
    echo "Service file created successfully at $SERVICE_FILE"
    
    # Reload systemd to recognize the new service
    echo "Reloading systemd daemon..."
    sudo systemctl daemon-reload
    
    # Enable the service to start at boot
    echo "Enabling service to start at boot..."
    sudo systemctl enable django-server.service
    
    # Start the service now
    echo "Starting the service..."
    sudo systemctl start django-server.service
    
    echo "Service setup completed successfully!"
    echo "You can check the status with: sudo systemctl status django-server.service"
else
    echo "Failed to create service file. Check permissions."
    exit 1
fi 