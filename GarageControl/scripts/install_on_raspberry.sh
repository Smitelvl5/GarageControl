#!/bin/bash
# Installation Script for Raspberry Pi
# This script installs all dependencies needed for the Django Server

echo "===== Django Server with Sensor Integration ====="
echo "Installing dependencies for Raspberry Pi..."
echo ""

# Update system
echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install required packages
echo "Installing required system packages..."
sudo apt install -y python3-pip python3-venv

# Install packages needed for weather scraping
echo "Installing packages for weather scraping functionality..."
sudo apt install -y chromium-browser chromium-chromedriver
sudo apt install -y xvfb  # Virtual framebuffer for headless browser

# Create virtual environment (optional but recommended)
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Make scripts executable
echo "Making scripts executable..."
chmod +x setup_raspberry_autostart.sh

# Create data and logs directories
echo "Creating data and logs directories..."
mkdir -p data logs
mkdir -p weather_cache

# Create .env file for configuration
echo "Creating environment configuration file..."
if [ ! -f .env ]; then
    echo "# Configuration for Govee Controller" > .env
    echo "GOVEE_API_KEY=your_api_key_here" >> .env
    echo "WEATHER_STATION_ID=your_weather_station_id_here" >> .env
    echo "# Find your local weather station ID at Weather Underground" >> .env
    echo "Created .env file. Please edit it to add your API keys."
else
    echo ".env file already exists, not overwriting."
fi

echo ""
echo "===== Installation Complete! ====="
echo ""
echo "To start the server manually:"
echo "  python manage.py runserver 0.0.0.0:8000"
echo ""
echo "To configure autostart at boot:"
echo "  ./setup_raspberry_autostart.sh"
echo ""
echo "Once started, access the dashboard at:"
echo "  http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "IMPORTANT: Edit the .env file to add your Govee API key and Weather Station ID."
echo ""
echo "Happy monitoring!" 