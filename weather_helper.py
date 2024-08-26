from datetime import datetime, timedelta
import logging
import urllib3
import json

def round_to_nearest_hour(timestamp):
    # Convert the timestamp to a datetime object
    dt = datetime.fromtimestamp(timestamp)
    
    # Determine whether to round up or down
    if dt.minute >= 30:
        dt = dt + timedelta(hours=1)
    
    # Set minutes, seconds, and microseconds to zero
    dt = dt.replace(minute=0, second=0, microsecond=0)
    
    return dt

def get_weather_data(lat, lng, start_time):
    # Initialize logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    try:
        # Convert start_time to Unix timestamp and round to the nearest hour
        start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        rounded_dt = round_to_nearest_hour(start_dt.timestamp())
        
        # Make the GET request to the weather API
        url = f"https://api.open-meteo.com/v1/forecast?hourly=temperature_2m&latitude={lat}&longitude={lng}&start_date={rounded_dt.date()}&end_date={rounded_dt.date()}&timezone=UTC"
        logger.info(f"weather url : {url}")
        
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        logger.info(f"response status: {response.status}")
        
        # Parse the JSON response
        weather_data = json.loads(response.data.decode('utf-8'))
        
        # Extract the hourly weather data
        elevation = weather_data['elevation']
        hourly_data = weather_data.get('hourly', {})
        time_series = hourly_data.get('time', [])
        temperature_series = hourly_data.get('temperature_2m', [])
        
        # Match the rounded start_time to the corresponding hourly data
        matching_temperature = None
        for i, time_str in enumerate(time_series):
            if datetime.strptime(time_str, "%Y-%m-%dT%H:%M") == rounded_dt:
                matching_temperature = temperature_series[i]
                break
        
        if matching_temperature is not None:
            logger.info(f"Matching temperature at {rounded_dt}: {matching_temperature}°C")
            matching_temperature_converted = (matching_temperature * 9/5) + 32
            elevation_converted = elevation * 3.28084
            return {
                "body": json.dumps({
                    "temperature": matching_temperature_converted,
                    "elevation": elevation_converted
                })
            }
        else:
            raise Exception("No matching weather data found for the given start time.")
    
    except Exception as e:
        logger.error(f"Error retrieving weather data: {str(e)}")
        raise