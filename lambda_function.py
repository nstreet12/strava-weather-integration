import json
import logging
import urllib3
import boto3
from botocore.exceptions import ClientError
from strava_helper import get_strava_activity, get_access_token, put_temperature_to_strava
from weather_helper import get_weather_data, round_to_nearest_hour

#Set up basic logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Check for GET method and 'hub.challenge' in the query parameters
    logger.info(f"Received event: {json.dumps(event)}")
    if event['httpMethod'] == 'GET' and 'hub.challenge' in event['queryStringParameters']:
        challenge = event['queryStringParameters']['hub.challenge']
        logger.info(f"Returning hub.challenge: {challenge}")
        return {
            "statusCode": 200,
            "body": json.dumps({"hub.challenge": challenge})
        }
    # For POST requests or other methods
    elif event['httpMethod'] == 'POST' and 'hub.challenge' in event['queryStringParameters']:
        body = json.loads(event['body'])
        logger.info(f"Parsed body: {body}")
        if 'hub.challenge' in body:
            return {
                "statusCode": 200,
                "body": json.dumps({"hub.challenge": body['hub.challenge']})
            }    
    elif 'object_id' in event['body']:
        logger.info(f"Received event: {json.dumps(event)}")
        body = json.loads(event['body'])
        logger.info(f"Parsed body: {body}")
        activity_id = body['object_id']
        aspect_type = body['aspect_type']
        logger.info(f"Get activity_id: {activity_id}, Get aspect_type: {aspect_type}")
        
        if aspect_type == 'create':
            activity_data = get_strava_activity(activity_id)
            body = json.loads(activity_data['body'])
            start_time = body['start_time']
            lat, lng = body['geo_location']
            
            weather_data = get_weather_data(lat, lng, start_time)
            
            return put_temperature_to_strava(activity_id, weather_data)
        else:
            pass
    else:
        pass