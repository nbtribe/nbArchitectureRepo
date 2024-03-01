import boto3
from botocore.exceptions import ClientError
import os




def check_files_exist(bucket_name, prefix):
    s3 = boto3.client('s3')

    try:
        # List objects in the specified bucket and prefix
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        print(response)

        # If there are no files found, return False
        if 'Contents' not in response:
            print("FAILED")
            status = "FAILED"
            return  {"filePresentStatus": status}

        # If there are files found, return True
        print("TRUE")
        status = True
        return  {"filePresentStatus": status}

    except Exception as e:
        print(f"An error occurred: {e}")
        status = "FAILED"
        return  {"filePresentStatus": status}

def lambda_handler(event, context):
    config = event["querystring"]
    deployment_buckt = config["deployment_bucket"]
    source_sys = config["source_system"]
    prefix = config["prefix"]
    source_sys = config["source_system"]
    customer = config["customer"]
    file_path = f"integrations/{source_sys}/{customer}/{prefix}"
    filePresentStatus = check_files_exist(deployment_buckt,file_path)
    return filePresentStatus
    
    
