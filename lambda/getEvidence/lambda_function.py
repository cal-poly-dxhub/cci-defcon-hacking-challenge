import json
import boto3
import logging
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#bucket name and the file name of the evidence
BUCKET = ""
EVIDENCE = ""

def lambda_handler(event, context):
    logger.info("event object: {}".format(event))
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    
    compDetails = dynamodb.Table('')
    
    response = {
        "isBase64Encoded": "false",
        "statusCode": 200,
        "headers": {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "PUT, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Date,X-Amzn-Trace-Id,x-amz-apigw-id,x-amzn-RequestId,Authorization"
        },
        "body": json.dumps({"error": None})
    }

    try:
        email = event['requestContext']['authorizer']['claims']['email']
        user = email.split('@')[0]
    except:
        return requestError(response, 400, "Cognito credentials not found in the request payload.")
    
    #if evidence is not needed for each room, delete lines 39-49 and change the value of line 55 to just `EVIDENCE`
    try:
        room = event['queryStringParameters']['room']
    except:
        return requestError(response, 400, "room is missing from the request parameters.")
    try:
        rooms = compDetails.get_item(Key={"Name": "RoomCodes"})['Item']['Value'].keys()
    except:
        return requestError(response, 500, "System codes have not been properly configured.")
    
    if room not in rooms:
        return requestError(response, 400, "Request room does not exist.")
    
    url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': BUCKET,
            'Key': room + "-" + EVIDENCE
        },
        ExpiresIn=60
    )
    logger.info("{0} is accessing data for the {1}".format(user, room))
    
    response['body'] = json.dumps({"url": url})
    return response


def requestError(response, status_code, body):
    response['statusCode'] = status_code
    error = { "error": body }
    logger.error("error: {}".format(body))
    response['body'] = json.dumps(error)
    return response
