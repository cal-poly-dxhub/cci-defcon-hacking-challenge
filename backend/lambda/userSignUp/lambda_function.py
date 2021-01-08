import json
import time
import boto3
import logging
import urllib
import datetime
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("event object: {}".format(event))
    
    #define DynamoDB resources here
    dynamodb = boto3.resource("dynamodb")
    
    registered = dynamodb.Table("")
    excluded = dynamodb.Table("")
    compDetails = dynamodb.Table("")
    
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
    
    body = eval(event['body'])
    logger.info("request body: {}".format(body))
    
    #----------------------------VALIDATE REQUEST-------------------------------
    
    #validate the registration time period
    if not checkValidTime(compDetails):
        return requestError(response, 401, "Registrations are not being accepted at this time.")
    
    #verify the request via reCaptcha 
    try:
        userToken = body['captchaToken']
        validateReCaptcha(userToken, compDetails)
    except KeyError:
        return requestError(response, 400, "reCaptcha token not found in request body.")
    except Exception as e:
        return requestError(response, 401, e.args[0])
    
    #perform custom throttling
    try:
        ip = event['requestContext']['identity']['sourceIp']
        if throttleRequest(ip):
            return requestError(response, 401, "A request has been made from this IP within the last 10 minutes. Please wait to make another request.")
    except KeyError:
        return requestError(response, 400, "IP not found in request payload.")

    #validate the number of registered users is less than 1000
    if registered.item_count >= 1000:
        return requestError(response, 400, "1000 user sign-up limit has been reached.")
    
    #--------------------------END VALIDATE REQUEST-----------------------------
    
    #Check that all of the correct attributes are provided
    #Return status code 400
    try:
        user = {
            "email": body["email"].lower(),
            "firstName": body["firstName"].lower(),
            "lastName": body["lastName"].lower(),
            "age": int(body["age"]),
            "gender": body["gender"].lower(),
            "affiliation": body["affiliation"].lower(),
            "zipcode": body["zipcode"],
            "country": body["country"].lower(),
            "ip":ip,
            "roomsUnlocked": False,
            "completed": False
        }
    except KeyError:
        return requestError(response, 400, "Some user attributes are missing from the request body.")
    except Exception as e:
        return requestError(response, 400, e.args[0])

    #------------------------------VALIDATE USER--------------------------------

    #Check if the provided first/last name are in the ExcludedUsers table
    checkNameExclusion = excluded.query(Select="COUNT",
        KeyConditionExpression=Key("lastName").eq(user['lastName']) & Key("firstName").eq(user['firstName']))
    logger.info("checking for name in excluded users here: {}".format(checkNameExclusion))
    
    if checkNameExclusion['Count'] > 0:
        return requestError(response, 401, "The listed name is registered with the CCIC 2020 and therefore is not authorized for participation.")

    #Check if the provided email is in the ExcludedUsers table
    checkEmailExclusion = excluded.scan(Select="COUNT",
        FilterExpression=Attr("email").eq(user['email']))
    logger.info("checking for email in excluded users here: {}".format(checkEmailExclusion))
    
    if checkEmailExclusion['Count'] > 0:
        return requestError(response, 401, "The listed email is registered with the CCIC 2020 and therefore is not authorized for participation.")
   
    #Check if the provided email is in the RegisteredUsers table
    registrationCheck = registered.query(Select="ALL_ATTRIBUTES",
        KeyConditionExpression=Key("email").eq(user['email']))
    logger.info("checking for email in registered users here: {}".format(registrationCheck))
    
    if registrationCheck['Count'] > 0:
        return requestError(response, 400, "The registered user already exists in our records.")
    
    #Create new record with values from request in the RegisteredUsers table
    insertion = registered.put_item(Item=user)
    if insertion['ResponseMetadata']['HTTPStatusCode'] != 200:
        return requestError(response, 500, "System error: A record could not be created for the given user at this time.")

    return response


#checkValidTime ->  pulls start/end time from DynamoDB to confirm that the current
#                   system time (UTC) falls within that interval.
#return ->          boolean (True => request made during a valid time)
def checkValidTime(compDetails):
    start = compDetails.get_item(Key={'Name': 'StartRegistrationUTC'})['Item']['Value']
    startTime = datetime.datetime.fromisoformat(start)
    end = compDetails.get_item(Key={'Name': 'EndRegistrationUTC'})['Item']['Value']
    endTime = datetime.datetime.fromisoformat(end)
    
    currentTime = datetime.datetime.utcnow()
    return startTime <= currentTime < endTime


#validateReCaptcha ->   combines a secret token and user-provided token to make
#                       a POST call to reCaptcha to provide authentication.
#return ->              None; Exception raised in the event of an error
def validateReCaptcha(userToken, compDetails):
    secretToken = compDetails.get_item(Key={'Name': 'captchaSecret'})['Item']['Value']
    captchaLink = "https://www.google.com/recaptcha/api/siteverify?response={0}&secret={1}".format(userToken, secretToken)
    
    result = urllib.request.urlopen(urllib.request.Request(url=captchaLink, method='POST'))
    responseBody = json.loads(result.read())
    logger.info("reCaptcha response body: {}".format(responseBody))
    if not responseBody['success']:
        raise Exception("reCaptcha error: " + ", ".join(responseBody['error-codes']))


#throttleRequest -> checks for previous requests that match the user's IP and
#                   verifies that the difference between timestamps is greater
#                   than 10 minutes
#return ->          boolean (True => should throttle request)
def throttleRequest(ip):
    #time.time() returns seconds since epoch
    ips = boto3.resource("dynamodb").Table("SignUpThrottle")
    item = {
        "ip": ip,
        "time": int(time.time())
    }

    checkIP = ips.query(Select="ALL_ATTRIBUTES",
                        KeyConditionExpression=Key("ip").eq(ip))
    if checkIP['Count'] == 0:
        ips.put_item(Item=item)
    else:
        ipTimes = [item['time'] for item in checkIP['Items']]
        if item['time'] - max(ipTimes) < 600: #check to see if a request was made within the last 10 minutes. (600 seconds)
            return True
        ips.put_item(Item=item)


#requestError ->    method to uniformly format errors for API response
#return ->          response object
def requestError(response, status_code, body):
    response['statusCode'] = status_code
    error = { "error": body }
    logger.error("error: {}".format(body))
    response['body'] = json.dumps(error)
    return response
