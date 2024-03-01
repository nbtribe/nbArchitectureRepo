# deploy cloudformation stack in bucket

import logging
import json
import boto3
import os
from botocore.exceptions import ClientError
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)


s3 = boto3.resource('s3')
cfn = boto3.client('cloudformation')


def lambda_handler(event, context):
    # print(event)
    logger.info(f'Received event: {json.dumps(event)}')
    # get object from event
    response = event['Records'][0]
    object_key = response['s3']['object']['key']
    print(object_key)

    bucket= os.environ.get("bucket_name")
    source_sys = os.environ.get("source_system")
    roleArn=os.environ.get("roleArn")


    content_object = s3.Object(bucket, object_key)
    file_content = content_object.get()['Body'].read().decode('utf-8')
    print(file_content)
    
    
    logger.info(
    f'Started provisioning tenant infrastructure for tenant {source_sys}')
    
    # params = [
    #     {"ParameterKey": "ParamTenantId", "ParameterValue": tenant_data["tenantId"]},
    #     {"ParameterKey": "ParamTenantName", "ParameterValue": tenant_data["tenantName"]}
    # ]
    
    cfn.create_stack(
        StackName=f'integration-{source_sys.replace("_","-")}-AutoDeployment',
        TemplateBody=file_content,
        # Parameters=params,
        Capabilities=['CAPABILITY_IAM'],
        RoleARN=roleArn,
    )

    return {
        "statusCode": 200,
        "body": json.dumps("Started provisioning integration infrastructure")

        }
    