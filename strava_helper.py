import os
import logging
import boto3
import urllib3
import json

#Set up basic logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_access_token(resource):
    if resource == "strava":
        client_id = os.environ.get('strava_client_id')
        client_secret = os.environ.get('strava_client_secret')
        refresh_token = os.environ.get('strava_refresh_token')
        # access_token = get_access_token()
        url = f"https://www.strava.com/oauth/token?client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}&grant_type=refresh_token"
        # headers = {"Authorization": f"Bearer {access_token}"}
        # data = {"text": comment}
        logger.info(f"url : {url}")
        
        # Create a PoolManager instance to make requests
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

    ######
    #Add Weather API access logic 
    ######
    
    else:
        raise Exception("No Secret Resource Found.")

def get_strava_activity(activity_id):
    try:
        access_token = get_access_token("strava", )
        logger.info(f"access token ({access_token}) made into get_strava_activity function")
        url = f"https://www.strava.com/api/v3/activities/{activity_id}/"
        headers = {"Authorization": f"Bearer {access_token}"}
        # data = {}
        logger.info(f"get activity url : {url}")
        
        # Create a PoolManager instance to make requests
        http = urllib3.PoolManager()
        
        # Make the POST request to Strava to get a new access token
        response = http.request('GET', url, headers=headers)
        logger.info(f"response: {response}")
        
        #Get needed activity Attributes: activity_id,location,start_time,end_time
        response_data = json.loads(response.data.decode('utf-8'))
        # logger.info(f"activity data json: {response_data}")
        activity_id = response_data['id']
        start_time = response_data['start_date']
        elapse_time_sec = response_data['elapsed_time']
        geo_location = response_data['start_latlng']
        logger.info(f"get attributes : {activity_id},{start_time},{elapse_time_sec},{geo_location}")
        if response.status == 200:
            return {
                "body": json.dumps({
                    "activity_id": activity_id,
                    "start_time": start_time,
                    "geo_location": geo_location
                })
            }
        else:
            raise Exception("Failed to post comment on Strava")
    except:
        raise Exception("GET Strava activity request unsuccessful.")


def put_temperature_to_strava(activity_id, weather):
    try:
        # Parse the JSON event to extract the temperature and elevation
        event_data = json.loads(weather['body'])
        temperature = event_data.get('temperature')
        elevation = event_data.get('elevation')
        
        # Retrieve the access token
        access_token = get_access_token("strava")
        logger.info(f"Access token ({access_token}) obtained in put_temperature_to_strava function")
        
        # Construct the request URL and headers
        url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        
        # Create the data to update the activity description with temperature and elevation
        description = f"Weather at activity start: Temperature: {temperature} (F) | Elevation: {elevation} ft"
        update_data = {
            "description": description
        }
        
        logger.info(f"Updating activity description with URL: {url}")
        
        # Make the PUT request to Strava
        http = urllib3.PoolManager()
        response = http.request('PUT', url, headers=headers, body=json.dumps(update_data))
        logger.info(f"Response status: {response.status}")
        
        # Check response status
        if response.status == 200:
            logger.info("Activity description successfully updated with weather details")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Activity description updated successfully",
                    "activity_id": activity_id
                })
            }
        else:
            raise Exception("Failed to update activity description on Strava")
    
    except Exception as e:
        logger.error(f"Error updating activity description on Strava: {str(e)}")
        raise Exception("PUT request to update activity description on Strava was unsuccessful.")
