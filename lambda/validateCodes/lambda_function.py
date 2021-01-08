import json, boto3, logging
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("event object: {}".format(event))
    
    dynamodb = boto3.resource("dynamodb")
    compDetails = dynamodb.Table("")
    registered = dynamodb.Table("")
    
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
    
    #validates cognito credentials
    try:
        email = event['requestContext']['authorizer']['claims']['email']
    except:
        return requestError(response, 400, "Cognito credentials not found in the request payload.")
    
    #a PUT indicates that codes are being submitted for validation
    if event['httpMethod'] == "PUT":
        #validate that the codes have been properly convigured in the DynamoDB table
        try:
            roomCodes = compDetails.get_item(Key={"Name": "RoomCodes"})['Item']['Value']
        except:
            return requestError(response, 500, "System codes have not been properly configured.")
        
        userCodes = event['queryStringParameters']
        
        #check that the ordered list of user-submitted room names matches the systems room names
        if sorted(roomCodes.keys()) != sorted(userCodes.keys()):
            return requestError(response, 400, "All codes were not found in the query string parameters.")
        
        #collect the user-submitted codes that do not match the submitted codes
        errors = []
        for room in userCodes.keys():
            if userCodes[room] != roomCodes[room]:
                errors.append(userCodes[room])
        
        if len(errors) > 0:
            return requestError(response, 401, "User code(s) [" + ", ".join(errors) + "] do not match the system codes.")
        
        unlockRoom = registered.update_item(
            Key={"email": email},
            UpdateExpression="set roomsUnlocked = :u",
            ExpressionAttributeValues={
                ":u": True
            }
        )
        logger.info("{0} unlocked the final room: {1}".format(email, unlockRoom))
    
    elif event['httpMethod'] == "GET":
        #verify that the codes are correctly configured as a (python) dictionary object
        try:
            roomCodes = compDetails.get_item(Key={"Name": "RoomCodes"})['Item']['Value']
            rooms = roomCodes.keys()
        except:
            return requestError(response, 500, "System codes have not been properly configured.")
        
        try:
            room = event['queryStringParameters']['room']
        except KeyError:
            return requestError(response, 400, "room is missing from the request parameters.")

        if room not in rooms:
                return requestError(response, 400, "The requested room does not exist")
        roomCode = roomCodes[room]
        response['body'] = json.dumps({"code": roomCode})
        
    else:
        return requestError(response, 400, "incorrect HTTP method. Only accepting GET/PUT.")
    return response
    

def requestError(response, status_code, body):
    response['statusCode'] = status_code
    error = { "error": body }
    logger.error("error: {}".format(body))
    response['body'] = json.dumps(error)
    return response
