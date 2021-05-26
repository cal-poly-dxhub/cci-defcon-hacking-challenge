# CCI DEFCON Hacking Competition
## Backend Architecture
The following web services were taken advantage of to form this solution:
- Amazon VPC
- Amazon API Gateway
- AWS Lambda
- Amazon DynamoDB
- AWS Step Functions

### Amazon API Gateway
The schema for the API gateway used within this solution is available [here](backend/api_gateway_def.json). 

### AWS Lambda
1. accessRooms

This enables a data-driven time constraint on a user accessing rooms. The start/end times are stored within a DynamoDB table and accessed over the AWS python SDK (boto3).

2. ec2Manager

This is responsible for all actions performed on an EC2 instance. The only input taken by the user is their cognito credentials and the proxy value found in the API request. The python libraries rsa and pyasn1 are imported locally to be used for password decryption of a windows admin password on the EC2 instance(s).

3. getCompetitionTime

This is a simple data-driven API lambda integration to grab the competition time.

4. getEvidence

This is a utility to return a pre-signed URL of an object with a a pre-defined bucket and key name.

5. userSignUp

This function performs a few manual API throttle attempts as well as a captcha link request before validating and then adding a user into a DynamoDB table.

6. validateCodes

Matches the request body to codes present within a DynamoDB table.

### AWS Step Functions

Part of the architecture of this application includes strict cost-management. Based on a pre-defined time period (X seconds), any EC2 instances launched through the ec2Manager have a timer set on them with AWS Step Functions. A call to ec2Manager (only performed by AWS Step Functions) to terminate the instance is delayed by X seconds while the user has access to their instance in the meantime.

### AWS Sumerian Scenes
You can download an export of all the Sumerian scenes here<br>
[Clean Room!](https://dxhub-static.calpoly.edu/media/defcon-sumerian/clean_room-gltf.zip)
[Control Room!](https://dxhub-static.calpoly.edu/media/defcon-sumerian/control_room-gltf.zip)
[Court Room!](https://dxhub-static.calpoly.edu/media/defcon-sumerian/court_room-gltf.zip)
[Crash Site!](https://dxhub-static.calpoly.edu/media/defcon-sumerian/crash_site-gltf.zip)
[Office Space!](https://dxhub-static.calpoly.edu/media/defcon-sumerian/office_space-gltf.zip)
