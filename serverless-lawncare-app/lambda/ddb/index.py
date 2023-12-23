import boto3
import os
import json
import logging
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb_client = boto3.client("dynamodb")


def handler(event, context):
    table = os.environ.get("TABLE_NAME")
    logging.info(f"## Loaded table name from environment variable DDB_TABLE: {table}")
    if event["body"]:
        item = json.loads(event["body"])
        logging.info(f"## Received payload: {item}")
        firstName = str(item["firstName"])
        lastName = str(item["lastName"])
        id = str(item["id"])
        phone = str(item["phone"])
        email = str(item["email"])
        isActive = bool(item["isActive"])
        dynamodb_client.put_item(
            TableName=table,
            Item={"firstName": {"S": firstName}, "lastName": {"S": lastName}, "id": {"S": id}, "phone": {"S": phone}, "email": {"S": email}, "isActive": {"Bool" : isActive}},
        )
        message = "Successfully inserted data!"
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": message}),
        }
    else:
        logging.info("## Received request without a payload")
        dynamodb_client.put_item(
            TableName=table,
            Item={
                "firstName": {"S": "Nate"}, 
                "lastName": {"S": "Brantley"}, 
                "id": {"S": str(uuid.uuid4())},
                "phone": {"S": "8034935704"}, 
                "email": {"S": "trybe.endeavors@gmail.com"}, 
                "isActive": {"Bool" : True}
                # "year": {"N": "2012"},
                # "title": {"S": "The Amazing Spider-Man 2"},
            },
        )
        message = "Successfully inserted data!"
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": message}),
        }