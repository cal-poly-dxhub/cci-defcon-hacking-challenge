import boto3
import logging
import json
import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    dynamodb = boto3.resource("dynamodb")
    compParams = dynamodb.Table("")
    
    response = {
        "isBase64Encoded": "false",
        "statusCode": 200,
        "headers": {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Date,X-Amzn-Trace-Id,x-amz-apigw-id,x-amzn-RequestId,Authorization"
        }
    }
    
    try:
        start = compParams.get_item(Key={'Name': 'StartChallengeUTC'})['Item']['Value']
        end = compParams.get_item(Key={'Name': 'EndChallengeUTC'})['Item']['Value']
    except Exception as e:
        logger.error(str(e))
        return requestError(response, 500, "start/end time could not be retrieved.")
    
    startTime = datetime.datetime.fromisoformat(start)
    endTime = datetime.datetime.fromisoformat(end)
    
    body = {
        "startTime": str(startTime),
        "endTime": str(endTime)
    }
    response['body'] = json.dumps(body)
    return response

def requestError(response, status_code, body):
    response['statusCode'] = str(status_code)
    error = { "error": body }
    logger.error(body)
    response['body'] = json.dumps(error)
    return response
