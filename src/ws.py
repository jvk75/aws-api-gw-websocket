import boto3
import json, sys, os
import requests

from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

awsregion = os.environ.get('AWS_REGION')

ddbtable = 'ddb-connections'
dynamodb = boto3.client('dynamodb', region_name=awsregion)

apiid = None
apiname = os.environ.get('WSAPINAME')
apis = boto3.client('apigatewayv2').get_apis()['Items']
for api in apis:
    if api['Name'] == apiname:
        apiid = api['ApiId']
        break

awsauth = BotoAWSRequestsAuth(aws_host=apiid + '.execute-api.' + awsregion + '.amazonaws.com', aws_region=awsregion, aws_service='execute-api')

##
def addId(connid):
    return dynamodb.put_item(TableName=ddbtable, Item={'Connections': {'S': connid}})

##
def removeId(connid):
    return dynamodb.delete_item(TableName=ddbtable, Key={'Connections': {'S': connid}})

##
def connect(event, context):
    try:
        connid = event['requestContext']['connectionId']
    except:
        return {"body": "error", "statusCode": 400}
    
    rsp = addId(connid)
    return {"body": "OK", "statusCode": 200}

##
def disconnect(event, context):
    try:
        connid = event['requestContext']['connectionId']
    except:
        return {"body": "error", "statusCode": 400}
    
    rsp = removeId(connid)
    return {"body": json.dumps(rsp), "statusCode": 200}

##
def postMessage(event, context):
    
    body = json.loads(event['body'])
    text = body['text']

    ddbrsp = dynamodb.scan(TableName=ddbtable)
    
    items = ddbrsp['Items']
    data = {'text': text, 'count': len(items)}
    url = 'https://' + apiid + '.execute-api.' + awsregion + '.amazonaws.com/test/@connections/'
    for item in items:
        conn = item['Connections']['S']
        rsp = requests.post(url + conn, data=json.dumps(data), auth=awsauth)
        if rsp.status_code == 410:
            removeId(conn)
    
    return {"body": "OK", "statusCode": 200}
