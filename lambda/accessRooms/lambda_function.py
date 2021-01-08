import json
import boto3
import datetime
import urllib

def lambda_handler(event, context):
    # Access proper DynamoDB table
    dynamodb = boto3.resource("dynamodb")
    values = dynamodb.Table("")

    # Obtain start/end timestamps (UTC) from DynamoDB for comparison
    startT = values.get_item(Key={'Name': 'StartTimeUTC'})['Item']['Value']
    startStamp = datetime.datetime.fromisoformat(startT)
    endT = values.get_item(Key={'Name': 'EndTimeUTC'})['Item']['Value']
    endStamp = datetime.datetime.fromisoformat(endT)
    
    # Check for potential error with provided start/end timestamps (UTC)
    if(startT >= endT):
        print("error")
    
    # Verify if current timestamp (UTC) is within the allowed timeframe
    currentT = datetime.datetime.utcnow().isoformat()
    if(startT <= currentT <= endT):
        # Present user with access to links to Sumerian rooms
        roomLink = values.get_item(Key={'Name': 'RoomLink'})['Item']['Value']
        responseBody = str("Link: " + roomLink)

        res = urllib.request.urlopen(urllib.request.Request(url=roomLink, headers={'Accept': 'application/json'}, method='GET'), timeout=5)
        print(res.status)
        print(res.reason)
    else:
        # Present user with message regarding when will be available
        responseBody = str("Welcome! The challenge will be available between " + 
            startStamp.strftime("%B %d %H:%M (UTC)") + " & " + endStamp.strftime("%B %d %H:%M (UTC)"))
            
    # Response for handler
    print(responseBody)
    return {
        'statusCode': 200,
        'body': json.dumps(responseBody)
    }
