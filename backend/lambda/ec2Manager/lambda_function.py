import boto3, logging, json
import datetime, time
import random
import rsa, base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TESTING = True

dynamodb = boto3.resource("dynamodb")
registered = dynamodb.Table("")
compParams = dynamodb.Table("")

#*********currently the master AMI with a default password for everyone*********
AMI = ""
INSTANCE_SIZE = ""
VOLUME_SIZE = 65 #in GB
S3 = ""
VPC = ""
SG = ""
STATE_MACHINE_ARN = ""
MAX_EC2_DURATION = int(compParams.get_item(Key={'Name': 'ChallengeDurationInHours'})['Item']['Value']) * 60 * 60 if not TESTING else 60 * 60 

def lambda_handler(event, context):
    logger.info('event info: {}'.format(event))
    
    #supplied with appropriate headers for CORS specifications
    response = {
        "isBase64Encoded": "false",
        "statusCode": 200,
        "headers": {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, PUT, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Date,X-Amzn-Trace-Id,x-amz-apigw-id,x-amzn-RequestId,Authorization"
        }
    }
    result = None
    
    #work-around for state machine to execute termination of instance (fully-managed server-side)
    instance = event.get("sm-instanceId")
    userEmail = event.get("sm-userEmail")
    if instance != None and userEmail != None:
        setComplete(userEmail)
        terminateInstance(instance)
        return response

    
    #Implement with Amazon Cognito in place
    try:
        email = event['requestContext']['authorizer']['claims']['email']
        user = email.split('@')[0]
    except KeyError:
        return requestError(response, 400, "missing user Cognito credentials/invalid email in request payload.")
    
    #checks that the user has already submitted previous room codes before accessing EC2 resources
    #BONUS: guarantees that this user is initialized within the system
    try:
        hasAccess = registered.get_item(Key={'email': email})['Item']['roomsUnlocked']
        if not hasAccess:
            return requestError(response, 401, "User has not submitted the necessary room codes to continue.")
    except KeyError:
        return requestError(response, 500, "User has not been properly initialized within our system.")
    
    #validate time
    if not TESTING and not checkValidTime(compParams):
        return requestError(response, 401, "instances cannot be interacted with at this time.")
    
    # Which path did we get from API Gateway indicating the method to execute?
    try:
        action = event['pathParameters']['proxy'].lower()
        logger.info("action: {}".format(action))
    except KeyError:
        logger.error("Missing action in event")
        return requestError(response, 400, "no action has been identified")
    
    
    totalInstances = describeInstances(user)
    liveInstances = describeInstances(user, live = True)
    logger.info("total instances: {}".format(totalInstances))
    logger.info("live instances: {}".format(liveInstances))
    
    #ensures that the current user
    if len(totalInstances) > 1 and not TESTING or len(liveInstances) > 1:
        return requestError(response, 400, "there exists more than 1 (live) instance tagged for this user.")
    
    if action == "init":
        if len(totalInstances) > 0 and not TESTING:
            return requestError(response, 400, "user cannot instantiate more than 1 instance.")
        elif not TESTING and checkValidTime(compParams) == False:
            return requestError(resopnse, 400, "user can no longer create an instance.")
        instance = createInstance(user)
        
        instanceDetails = {
            "instanceId": instance.instance_id,
            "launchTime": str(instance.launch_time),
            "publicIpAddress": instance.public_ip_address,
            "state": instance.state,
            "stateReason": instance.state_reason,
            "endTime": str(datetime.datetime.utcnow() + datetime.timedelta(seconds=MAX_EC2_DURATION))
        }
        setTimer(email, instanceDetails['instanceId'], MAX_EC2_DURATION)
        result = instanceDetails
    
    elif action == "reboot":
        try:
            if len(liveInstances) < 1:
                return requestError(response, 400, "no live instance(s) to reboot.")
            instances = [instance.id for instance in liveInstances]
            result = rebootInstance(instances)
        except Exception as e:
            logger.error(str(e))
            return requestError(response, 500, "instance(s) could not be rebooted.")
    
    elif action == "stop":
        try:
            if len(liveInstances) < 1:
                return requestError(response, 400, "no live instance(s) to stop.")
            instances = [instance.id for instance in liveInstances]
            result = stopInstance(instances)
            
            setComplete(email)
        except Exception as e:
            logger.error(str(e))
            return requestError(response, 500, "instance(s) could not be stopped.")
    
    #elif action == "terminate": #***if being re-implemented, code will need to be adapted to latest changes***
    #    try:
    #        if len(liveInstances) != 1:
    #            return requestError(response, 400, "no instance(s) to terminate.")
    #        instances = [instance.id for instance in liveInstances]
    #        result = terminate_instance(instances)
    #    except Exception as e:
    #        logger.error(str(e))
    #        return requestError(response, 500, "instance(s) could not be rebooted.")
    
    elif action == "password":
        try:
            if len(liveInstances) < 1:
                return requestError(response, 400, "no live instances(s) to report password.")
            result = {"password": compParams.get_item(Key={'Name': 'serverPassword'})['Item']['Value']}#getPassword(user, liveInstances[0].id)
        except Exception as e:
            logger.error(str(e))
            return requestError(response, 500, "password for instance(s) could not be reported.")
    
    elif action == "ip":
        try:
            if len(liveInstances) < 1:
                return requestError(response, 400, "no instances(s) to report public IP.")
            result = getPublicIP(liveInstances[0])
        except Exception as e:
            logger.error(str(e))
            return requestError(response, 500, "ip for instance(s) could not be reported.")
    
    elif action == "state":
        try:
            if len(totalInstances) < 1:
                return requestError(response, 400, "no instance(s) to report status.")
            result = getState(totalInstances[0])
        except Exception as e:
            logger.error(str(e))
            return requestError(response, 500, "state for instance(s) could not be reported.")

    elif action == "end":
        try:
            if len(totalInstances) < 1:
                return requestError(response, 400, "no instance(s) to report endTime.")
            result = getEndTime(totalInstances[0])
        except Exception as e:
            logger.error(str(e))
            return requestError(response, 500, "End time for instance could not be reported.")

    elif action == "unlocked":
        result = {"unlocked" : registered.get_item(Key={'email': email})['Item']['roomsUnlocked']}
    
    elif action == "completed":
        result = {"completed" : registered.get_item(Key={'email': email})['Item']['completed']}

    else:
        return requestError(response, 404, "unknown action requested")
    
    response['body'] = json.dumps(result)
    return response


def checkValidTime(compParams):
    start = compParams.get_item(Key={'Name': 'StartChallengeUTC'})['Item']['Value']
    end = compParams.get_item(Key={'Name': 'EndChallengeUTC'})['Item']['Value']
    
    startTime = datetime.datetime.fromisoformat(start)
    endTime = datetime.datetime.fromisoformat(end)
    currentTime = datetime.datetime.utcnow()
    return startTime <= currentTime <= (endTime - datetime.timedelta(MAX_EC2_DURATION))


def getEndTime(instance):
    launchTime = instance.launch_time
    endTime = launchTime + datetime.timedelta(seconds=MAX_EC2_DURATION)
    return {"endTime": str(endTime)}


#returns the subnet id from a set of subnets based on a uniformly distributed random variable
def setSubnet():
    EC2 = boto3.resource("ec2")
    vpc = EC2.Vpc(VPC)
    
    subnets = [subnet for subnet in vpc.subnets.all()]
    count = len(subnets)
    subnet = subnets[random.randrange(count)]
    return subnet.id
 

def setComplete(email):
    complete = registered.update_item(
            Key={"email": email},
            UpdateExpression="set completed = :u",
            ExpressionAttributeValues={
                ":u": True
            }
        )
    logger.info("{0} completed the challenge: {1}".format(email, complete))


#returns an array of EC2 Instance objects
def describeInstances(user, live = None):
    EC2 = boto3.resource("ec2")
    userFilter = {
        "Name": "tag:Name",
        "Values": [user]
    }
    if live != None: #intend to only find live/terminated or stopped instances
        states = ["running",  "pending", "shutting-down"] if live else ["stopping", "stopped", "terminated"]
        instanceState = {
            "Name": "instance-state-name",
            "Values": states
        }
        return [instance for instance in EC2.instances.filter(Filters=[userFilter, instanceState])]
    return [instance for instance in EC2.instances.filter(Filters=[userFilter])]


def rebootInstance(instanceList):
    EC2 = boto3.client("ec2")
    response = EC2.reboot_instances(InstanceIds=instanceList)
    return response


def stopInstance(instanceList):
    EC2 = boto3.client("ec2")
    response = EC2.stop_instances(InstanceIds=instanceList)
    return response


def getPassword(user, instanceId):
    EC2 = boto3.client("ec2")
    respBody = {"password": None}
    response = EC2.get_password_data(InstanceId=instanceId)
    if not response['PasswordData']:
        respBody['password'] = ""
        return respBody
    
    keyName = getKeyName(user)
    pwData = base64.b64decode(response['PasswordData'])
    userEC2Key = getKeyData(keyName)

    privateKey = rsa.PrivateKey.load_pkcs1(userEC2Key)
    key = rsa.decrypt(pwData, privateKey).decode('utf-8')

    respBody['password'] = key
    return respBody


def getPublicIP(instance):
    return {"ipAddress": instance.public_ip_address}


def getState(instance):
   return {"state": instance.state}


def createInstance(user):
    EC2 = boto3.resource("ec2")
    create_key(user)
    
    newInstance = EC2.create_instances(
        ImageId=AMI,
        MinCount=1,
        MaxCount=1,
        InstanceType=INSTANCE_SIZE,
        KeyName=getKeyName(user),
        SubnetId=setSubnet(),
        SecurityGroupIds=[SG],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{
                    'Key': 'Name',
                    'Value': user
                }]
            }
        ],
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'VolumeSize': VOLUME_SIZE,
                    'VolumeType': 'gp2'
                }
            }
        ]
    )
    logger.info("instance created for {0}: {1}".format(user, newInstance[0]))
    return newInstance[0]


def getKeyData(user):
    s3 = boto3.client('s3')
    key = s3.get_object(Bucket=S3,
                            Key=user)
    logger.info("key info: {}".format(key))
    keyData = key['Body'].read()
    return keyData
    

def getKeyName(user):
    return "{}-defcon".format(user)


def create_key(user):
    # Check to see this user has a key generated
    ec2 = boto3.client('ec2')
    response = ec2.describe_key_pairs()
    keyPairs = response['KeyPairs']
    keyName = getKeyName(user)
    createKey = True
    
    for key in keyPairs:
        # user key found no need to create
        if key['KeyName'] == keyName:
            createKey = False
            break
        
    s3 = boto3.client('s3')
    if createKey:
        response = ec2.create_key_pair(KeyName=keyName)
    
        id = None
        logger.info("Bucket %s, Key=%s", S3, keyName)
        # Write id to S3
        id = s3.put_object(Body=response['KeyMaterial'], Bucket=S3, Key=keyName)
    else:
        #this ensures that the key exists in the S3 bucket as well (and not just as an EC2 key pair)
        try:
            key = s3.get_object(Bucket=S3, Key=keyName)
        except:
            logger.info("key was not found in S3 bucket. Replacement being configured...")
            ec2.delete_key_pair(KeyName=keyName)
            response = ec2.create_key_pair(KeyName=keyName)
            logger.info("key info: {}".format(response))
            s3.put_object(Body=response['KeyMaterial'], Bucket=S3, Key=keyName)


def requestError(response, status_code, body):
    response['statusCode'] = str(status_code)
    error = { "error": body }
    logger.error(body)
    response['body'] = json.dumps(error)
    return response

#---------------------------STEP FUNCTION METHODS-------------------------------
def setTimer(email, instanceId, waitPeriod):
    user = email.split('@')[0]
    client = boto3.client('stepfunctions')
    body = '{"sm-instanceId": "' + instanceId + '", "waitPeriod": "' + str(waitPeriod) + '", "sm-userEmail": "' + email + '"}'
    response = client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=user if not TESTING else user + "_" + str(datetime.datetime.utcnow()).replace(" ", "_").replace(":", "-"),
        input=str(body))

def terminateInstance(instanceId):
    EC2 = boto3.client("ec2")
    #check that the state is not terminated before executing the following command
    EC2.terminate_instances(InstanceIds=[instanceId])
#-------------------------END STEP FUNCTION METHODS-----------------------------
