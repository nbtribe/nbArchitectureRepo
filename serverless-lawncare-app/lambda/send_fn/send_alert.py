import logging
import json
import boto3
import os

from botocore.exceptions import ClientError


def lambda_handler(event, context):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info("request: " + json.dumps(event))
    a = json.dumps(event)
    result = json.loads(a)
    notification = result["message"]

    topic_arn = os.environ.get('SNS_TOPIC_ARN')

    sns_client = boto3.client("sns")

    try:
        sent_message = sns_client.publish(
            TargetArn=topic_arn,
            # Message=json.dumps({'default': json.dumps(event)})
            Message=notification
        )
        
    

        if sent_message is not None:
            logger.info(f"Success - Message ID: {sent_message['MessageId']}")
        return {
            "statusCode": 200,
            "body": json.dumps(event)
        }

    except ClientError as e:
        logger.error(e)
        return None
