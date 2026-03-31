import os
import logging
import boto3
import urllib3
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_access_token(resource):
    if resource == "strava":
        client_id = os.environ.get('strava_client_id')
        client_secret = os.environ.get('strava_client_secret')
        refresh_token = os.environ.get('strava_refresh_token')
        url = f"https://www.strava.com/oauth/token?client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}&grant_type=refresh_token"
        logger.info(f"url : {url}")
        
        http = urllib3.PoolManager()
        
        # Make the POST request to Strava to get a new access token
        response = http.request('POST', url)
        
        # Decode and parse the response data
        response_data = json.loads(response.data.decode('utf-8'))
        logger.info(f"Access token response: {response_data}")
        
        # Extract the access token from the response data
        if 'access_token' in response_data:
            return response_data['access_token']
        else:
            raise Exception("Cannot find access token in response.")    
    else:
        raise Exception("No Secret Resource Found.")

def get_strava_activity(activity_id):
    try:
        access_token = get_access_token("strava")
        logger.info(f"access token ({access_token}) made into get_strava_activity function")
        url = f"https://www.strava.com/api/v3/activities/{activity_id}/"
        headers = {"Authorization": f"Bearer {access_token}"}
        logger.info(f"get activity url : {url}")
        
        http = urllib3.PoolManager()
        
        # Make the POST request to Strava to get a new access token
        response = http.request('GET', url, headers=headers)
        logger.info(f"response: {response}")
        
        # Get needed activity attributes
        response_data = json.loads(response.data.decode('utf-8'))
        activity_id        = response_data['id']
        activity_name      = response_data.get('name', '')
        activity_type      = response_data.get('type', '')
        sport_type         = response_data.get('sport_type', activity_type)
        start_time         = response_data['start_date']
        elapsed_time_sec   = response_data.get('elapsed_time', 0)
        moving_time_sec    = response_data.get('moving_time', elapsed_time_sec)
        distance_m         = response_data.get('distance', 0)
        elevation_gain_m   = response_data.get('total_elevation_gain', 0)
        elev_high_m        = response_data.get('elev_high')
        elev_low_m         = response_data.get('elev_low')
        avg_speed_ms       = response_data.get('average_speed', 0)
        max_speed_ms       = response_data.get('max_speed', 0)
        calories           = response_data.get('calories')
        pr_count           = response_data.get('pr_count', 0)
        suffer_score       = response_data.get('suffer_score')
        avg_watts          = response_data.get('average_watts')
        avg_cadence        = response_data.get('average_cadence')
        geo_location       = response_data['start_latlng']
        logger.info(f"get attributes : {activity_id},{start_time},{elapsed_time_sec},{geo_location}")
        if response.status == 200:
            return {
                "body": json.dumps({
                    "activity_id":           activity_id,
                    "name":                  activity_name,
                    "type":                  activity_type,
                    "sport_type":            sport_type,
                    "distance":              round(distance_m / 1000, 2),
                    "elevation_gain":        elevation_gain_m,
                    "elev_high":             elev_high_m,
                    "elev_low":              elev_low_m,
                    "elapsed_time_minutes":  round(elapsed_time_sec / 60, 1),
                    "moving_time_minutes":   round(moving_time_sec / 60, 1),
                    "avg_speed_kmh":         round(avg_speed_ms * 3.6, 1),
                    "max_speed_kmh":         round(max_speed_ms * 3.6, 1),
                    "calories":              calories,
                    "pr_count":              pr_count,
                    "suffer_score":          suffer_score,
                    "avg_watts":             avg_watts,
                    "avg_cadence":           avg_cadence,
                    "start_time":            start_time,
                    "geo_location":          geo_location
                })
            }
        else:
            raise Exception("Failed to post comment on Strava")
    except:
        raise Exception("GET Strava activity request unsuccessful.")


def put_data_to_strava(activity_id, ai_title, weather):
    try:
        # Parse the JSON event to extract the temperature and elevation
        event_data = json.loads(weather['body'])
        temperature = round(event_data.get('temperature'))
        elevation = round(event_data.get('elevation'))

        # Retrieve the access token
        access_token = get_access_token("strava")
        logger.info(f"Access token ({access_token}) obtained in put_data_to_strava function")

        # Construct the request URL and headers
        url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        # Update both name (AI-generated title) and description (weather details)
        description = f"Temperature (F): {temperature} | Elevation (ft): {elevation}"
        update_data = {
            "name": ai_title,
            "description": description
        }
        
        logger.info(f"Updating activity description with URL: {url}")
        
        # Make the PUT request to Strava
        http = urllib3.PoolManager()
        response = http.request('PUT', url, headers=headers, body=json.dumps(update_data))
        logger.info(f"Response status: {response.status}")
        
        # Check response status
        if response.status == 200:
            logger.info("Activity title and description successfully updated")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Activity updated successfully",
                    "activity_id": activity_id
                })
            }
        else:
            raise Exception("Failed to update activity description on Strava")
    
    except Exception as e:
        logger.error(f"Error updating activity description on Strava: {str(e)}")
        raise Exception("PUT request to update activity description on Strava was unsuccessful.")
