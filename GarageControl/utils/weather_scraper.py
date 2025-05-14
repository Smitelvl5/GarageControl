import time
import pandas as pd
import concurrent.futures
from datetime import datetime, timedelta, date
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import os
import json
import re
import requests
from pathlib import Path
from selenium.common.exceptions import NoSuchElementException
import logging

# Calculate the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the cache directory relative to the project root
CACHE_DIR = os.path.join(BASE_DIR, 'weather_cache')

# Create the cache directory if it doesn't exist
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Default station ID from environment variable
DEFAULT_STATION_ID = os.getenv('STATION', 'KTNMEMPH176')

# Set up logging
logger = logging.getLogger(__name__)

# Get current date (without hardcoding to 2023)
def get_current_date():
    """Get the current date"""
    return datetime.now().date()

def get_previous_date():
    """Get yesterday's date"""
    return datetime.now().date() - timedelta(days=1)

def scrape_weather_data(station_id, date_str):
    """
    Scrape weather data from Weather Underground for a specific date using Selenium

    Args:
        station_id (str): The PWS station ID (e.g., 'KTNBARTL92')
        date_str (str): Date in format YYYY-MM-DD

    Returns:
        DataFrame: Pandas DataFrame with the weather data
    """
    # Check cache first
    cache_file = os.path.join(CACHE_DIR, f"{station_id}_{date_str}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                print(f"Using cached data for {date_str}")
                return pd.DataFrame(cached_data)
        except Exception as e:
            print(f"Error reading cache: {e}")
            # Continue to scrape if cache read fails
    
    url = f"https://www.wunderground.com/dashboard/pws/{station_id}/table/{date_str}/{date_str}/daily"

    print(f"Setting up Chrome browser...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no browser UI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Comment out the binary location which is for Raspberry Pi
    # chrome_options.binary_location = "/usr/bin/chromium-browser"

    try:
        # Try to use the webdriver_manager directly instead of system chromedriver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=chrome_options
        )
    except Exception as e:
        print(f"Could not use webdriver_manager: {e}")
        # Fall back to default Chrome driver
        driver = webdriver.Chrome(options=chrome_options)

    try:
        print(f"Fetching data from {url}")
        driver.get(url)

        # Wait for the page to load (adjust timeout as needed)
        time.sleep(5)  # Initial wait for page to load

        # Wait for the table to be present
        wait = WebDriverWait(driver, 30)

        # Find all tables on the page and use the one that contains weather data
        tables = driver.find_elements(By.TAG_NAME, "table")

        if not tables:
            print("Error: Could not find any tables on the page.")
            driver.save_screenshot("debug_screenshot.png")
            print("Saved screenshot to debug_screenshot.png")

            # Save page source for debugging
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Saved page source to debug_page_source.html")
            return None

        # Find the table with weather data (usually the largest table)
        weather_table = None
        max_rows = 0

        for table in tables:
            rows = table.find_elements(By.TAG_NAME, "tr")
            if len(rows) > max_rows:
                max_rows = len(rows)
                weather_table = table

        if not weather_table:
            print("Error: Could not identify the weather data table.")
            return None

        # Extract headers
        headers = []
        header_elements = weather_table.find_elements(By.TAG_NAME, "th")
        for header in header_elements:
            headers.append(header.text.strip())

        # Extract rows
        rows = []
        data_rows = weather_table.find_elements(By.TAG_NAME, "tr")[
            1:
        ]  # Skip header row

        for row_element in data_rows:
            cells = row_element.find_elements(By.TAG_NAME, "td")
            row_data = [cell.text.strip() for cell in cells]
            if row_data:  # Only add non-empty rows
                rows.append(row_data)

        # Create DataFrame
        if headers and rows:
            # Make sure the number of columns match
            # If headers are fewer than the columns in rows, add generic column names
            while len(headers) < len(rows[0]):
                headers.append(f"Column_{len(headers)}")

            df = pd.DataFrame(rows, columns=headers)
            
            # Cache the data
            try:
                df_dict = df.to_dict('records')
                with open(cache_file, 'w') as f:
                    json.dump(df_dict, f)
                print(f"Cached data for {date_str}")
            except Exception as e:
                print(f"Error caching data: {e}")
                
            return df
        else:
            print("Error: Failed to extract data from the table.")
            return None

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None
    finally:
        # Always close the driver
        driver.quit()


def scrape_multiple_days(station_id, dates):
    """
    Scrape weather data for multiple dates in parallel using threads

    Args:
        station_id (str): The PWS station ID
        dates (list): List of date strings in format YYYY-MM-DD

    Returns:
        DataFrame: Combined Pandas DataFrame with the weather data for all dates
    """
    results = {}

    def scrape_worker(date):
        print(f"Starting thread for date: {date}")
        result = scrape_weather_data(station_id, date)
        if result is not None:
            result["Date"] = date
        return date, result

    # Use ThreadPoolExecutor to run scraping in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit scraping tasks
        future_to_date = {executor.submit(scrape_worker, date): date for date in dates}

        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_date):
            date = future_to_date[future]
            try:
                date, result = future.result()
                if result is not None:
                    results[date] = result
                    print(f"Successfully scraped data for {date}")
                else:
                    print(f"Failed to scrape data for {date}")
            except Exception as exc:
                print(f"Thread for {date} generated an exception: {exc}")

    # Combine all dataframes
    if results:
        combined_df = pd.concat(results.values(), ignore_index=True)
        return combined_df
    return None


def get_date_range(start_date_str, end_date_str=None):
    """
    Generate a list of dates between start_date and end_date inclusive

    Args:
        start_date_str (str): Start date in format YYYY-MM-DD
        end_date_str (str, optional): End date in format YYYY-MM-DD.
                                     If None, only start_date is returned.

    Returns:
        list: List of date strings in format YYYY-MM-DD
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)
        return date_list
    else:
        return [start_date_str]

def create_offline_response(station_id):
    """Create an offline response"""
    return {
        'temperature': None,
        'humidity': None,
        'dew_point': None,
        'wind_direction': None,
        'wind_speed': None,
        'wind_gust': None,
        'pressure': None,
        'precip_rate': None,
        'precip_accum': None, 
        'uv': None,
        'timestamp': datetime.now().isoformat(),
        'station_id': station_id,
        'status': 'offline'
    }

def scrape_weather_site(station_id=None):
    """
    Scrape comprehensive weather data from Weather Underground for a specific station.
    Returns a dictionary with all available weather data fields.
    """
    # Use provided station_id or fall back to environment variable
    if station_id is None:
        station_id = DEFAULT_STATION_ID
        
    # Get both today's and yesterday's dates for a full 24-hour dataset
    today = get_current_date()
    yesterday = get_previous_date()
    today_str = today.strftime('%Y-%m-%d')
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    # Log the current date that will be used
    print(f"Attempting to scrape data for today: {today_str}")
    
    # Use today's date for caching
    cache_file = os.path.join(CACHE_DIR, f"{station_id}_{today_str}.json")
    
    # Check for cached data less than 15 minutes old
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Get the age of the cache in minutes
            cache_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01T00:00:00'))
            now = datetime.now()
            age_minutes = (now - cache_time).total_seconds() / 60
            
            if age_minutes < 15:  # 15 minutes
                print(f"Using cached data ({int(age_minutes)} minutes old)")
                return data
                
            print(f"Cache is {int(age_minutes)} minutes old, fetching fresh data")
        except Exception as e:
            print(f"Error reading cache: {e}")
    
    # Try Selenium method first - robust but resource intensive
    try:
        print(f"Using Selenium to scrape latest weather data...")
        
        # First try today's data
        url = f"https://www.wunderground.com/dashboard/pws/{station_id}/table/{today_str}/{today_str}/daily"
        print(f"Trying today's data: {url}")
        
        # Set up headless Chrome browser
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize Chrome driver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        try:
            # Try today's data first
            driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # If today's data isn't available or is empty, try yesterday's data
            if "No data available" in driver.page_source or not driver.find_elements(By.TAG_NAME, "table"):
                print("No data for today, trying yesterday's data instead")
                yesterday_url = f"https://www.wunderground.com/dashboard/pws/{station_id}/table/{yesterday_str}/{yesterday_str}/daily"
                driver.get(yesterday_url)
                time.sleep(5)  # Wait for page to load
            
            # Find all tables
            tables = driver.find_elements(By.TAG_NAME, "table")
            
            if not tables:
                print("No tables found on the page")
                driver.save_screenshot(os.path.join(CACHE_DIR, "debug_screenshot.png"))
                with open(os.path.join(CACHE_DIR, "debug_page_source.html"), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
            else:
                # Find the table with weather data (usually the largest)
                weather_table = None
                max_rows = 0
                
                for table in tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    if len(rows) > max_rows:
                        max_rows = len(rows)
                        weather_table = table
                
                if weather_table:
                    # Get headers
                    header_row = weather_table.find_elements(By.TAG_NAME, "tr")[0]
                    headers = [h.text.strip() for h in header_row.find_elements(By.TAG_NAME, "th")]
                    print(f"Found table headers: {headers}")
                    
                    # Extract the last row (most recent data)
                    rows = weather_table.find_elements(By.TAG_NAME, "tr")
                    if len(rows) > 1:  # First row is usually headers
                        last_row = rows[-1]
                        cells = last_row.find_elements(By.TAG_NAME, "td")
                        
                        if cells:
                            # Extract all data fields
                            time_str = cells[0].text.strip() if len(cells) > 0 else "N/A"
                            
                            # Initialize data dictionary
                            data = {
                                'time': time_str,
                                'temperature': None,
                                'dew_point': None,
                                'humidity': None,
                                'wind_direction': None,
                                'wind_speed': None,
                                'wind_gust': None,
                                'pressure': None,
                                'precip_rate': None,
                                'precip_accum': None,
                                'uv': None,
                                'timestamp': datetime.now().isoformat(),
                                'station_id': station_id,
                                'status': 'online'
                            }
                            
                            # Extract values based on headers
                            for i, header in enumerate(headers):
                                if i < len(cells):
                                    cell_text = cells[i].text.strip()
                                    
                                    # Temperature
                                    if "Temperature" in header:
                                        temp_match = re.search(r'(\d+\.\d+)\s*°F', cell_text)
                                        if temp_match:
                                            data['temperature'] = float(temp_match.group(1))
                                    
                                    # Dew Point
                                    elif "Dew Point" in header:
                                        dew_match = re.search(r'(\d+\.\d+)\s*°F', cell_text)
                                        if dew_match:
                                            data['dew_point'] = float(dew_match.group(1))
                                    
                                    # Humidity
                                    elif "Humidity" in header:
                                        hum_match = re.search(r'(\d+)\s*%', cell_text)
                                        if hum_match:
                                            data['humidity'] = int(hum_match.group(1))
                                    
                                    # Wind Direction
                                    elif "Wind" in header and "Speed" not in header and "Gust" not in header:
                                        data['wind_direction'] = cell_text
                                    
                                    # Wind Speed
                                    elif "Speed" in header:
                                        speed_match = re.search(r'(\d+\.\d+)\s*mph', cell_text)
                                        if speed_match:
                                            data['wind_speed'] = float(speed_match.group(1))
                                    
                                    # Wind Gust
                                    elif "Gust" in header:
                                        gust_match = re.search(r'(\d+\.\d+)\s*mph', cell_text)
                                        if gust_match:
                                            data['wind_gust'] = float(gust_match.group(1))
                                    
                                    # Pressure
                                    elif "Pressure" in header:
                                        pres_match = re.search(r'(\d+\.\d+)\s*in', cell_text)
                                        if pres_match:
                                            data['pressure'] = float(pres_match.group(1))
                                    
                                    # Precipitation Rate
                                    elif "Precip. Rate" in header:
                                        rate_match = re.search(r'(\d+\.\d+)\s*in', cell_text)
                                        if rate_match:
                                            data['precip_rate'] = float(rate_match.group(1))
                                    
                                    # Precipitation Accumulation
                                    elif "Precip. Accum" in header:
                                        accum_match = re.search(r'(\d+\.\d+)\s*in', cell_text)
                                        if accum_match:
                                            data['precip_accum'] = float(accum_match.group(1))
                                    
                                    # UV
                                    elif "UV" in header:
                                        if cell_text and cell_text != "w/m²":
                                            try:
                                                data['uv'] = float(cell_text)
                                            except ValueError:
                                                data['uv'] = cell_text
                            
                            print(f"Extracted all weather data: {data}")
                            
                            # Cache the data
                            with open(cache_file, 'w') as f:
                                json.dump(data, f)
                            
                            return data
        
        finally:
            # Always close the driver
            driver.quit()
    
    except Exception as selenium_error:
        print(f"Selenium error: {selenium_error}")
    
    # Return offline response if all methods fail
    print("All scraping methods failed, returning offline status")
    return create_offline_response(station_id)

def get_latest_outdoor_temperature(station_id):
    """
    Get the latest outdoor temperature and weather data from Weather Underground
    
    Args:
        station_id (str): Weather Underground station ID (e.g., 'KTNMEMPH176')
        
    Returns:
        dict: Weather data including temperature, humidity, and other metrics
    """
    url = f"https://api.weather.com/v2/pws/observations/current?stationId={station_id}&format=json&units=e&apiKey=e1f10a1e78da46f5b10a1e78da96f525"
    
    try:
        logger.info(f"Fetching weather data for station {station_id}")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract the relevant data from the response
            obs = data.get('observations', [{}])[0]
            if not obs:
                logger.error("No observations found in weather data")
                return None
                
            # Extract all available weather metrics
            weather_data = {
                'temperature': obs.get('imperial', {}).get('temp'),
                'humidity': obs.get('humidity'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'time': obs.get('obsTimeLocal'),
                'status': 'online',
                'dew_point': obs.get('imperial', {}).get('dewpt'),
                'wind_direction': obs.get('winddir'),
                'wind_speed': obs.get('imperial', {}).get('windSpeed'),
                'wind_gust': obs.get('imperial', {}).get('windGust'),
                'pressure': obs.get('imperial', {}).get('pressure'),
                'precip_rate': obs.get('imperial', {}).get('precipRate'),
                'precip_accum': obs.get('imperial', {}).get('precipTotal'),
                'uv': obs.get('uv')
            }
            
            logger.info(f"Retrieved weather data: Temp={weather_data['temperature']}°F, Humidity={weather_data['humidity']}%")
            return weather_data
        else:
            logger.error(f"Error fetching weather data: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching weather data: {str(e)}")
        return None

if __name__ == "__main__":
    # For testing the module independently
    logging.basicConfig(level=logging.INFO)
    station_id = "KTNMEMPH176"  # Example station ID
    data = get_latest_outdoor_temperature(station_id)
    
    if data:
        print(f"Current weather at {station_id}:")
        print(f"Temperature: {data['temperature']}°F")
        print(f"Humidity: {data['humidity']}%")
        for key, value in data.items():
            if key not in ['temperature', 'humidity']:
                print(f"{key}: {value}")
    else:
        print("Unable to retrieve weather data") 