import boto3
import os
from datetime import datetime 
import sys
import json
import io
import gzip

source_bucket = os.environ["SOURCE_BUCKET"]
destination_bucket = os.environ["DESTINATION_BUCKET"]
destination_prefix = os.environ["DEST_PREFIX"]
source_prefix = os.environ["SOURCE_PREFIX"]
customer = os.environ["CUSTOMER"]
source_sys = os.environ["SOURCE_SYS"]
required_files = os.environ["REQUIRED_FILES"]
required_files_list = list(required_files.split(";"))

print(required_files_list)


def update_copy_script():
    template_key = f'{customer.lower()}_{source_sys}_copy_template.sql'
    scripts_folder = 'scripts/'
    print(f"template_key = {template_key}")
    # Create an S3 client
    s3 = boto3.client('s3')

    try:
        # Get the template file content from S3
        response = s3.get_object(Bucket=destination_bucket, Key=f"{scripts_folder}{template_key}")
        template_content = response['Body'].read().decode('utf-8')

        # Replace the placeholder with the current date
        current_date = datetime.now().strftime('%Y%m%d')
        new_content = template_content.replace('{datefolder}', current_date)

        # # Create a new file key for the destination
        new_file_key= f"{scripts_folder}{customer}_{source_sys}_copy.sql"

        # Upload the new content to the destination in S3
        s3.put_object(Body=new_content.encode('utf-8'), Bucket=destination_bucket, Key=new_file_key)

        print(f"New file created and uploaded to: s3://{destination_bucket}/{new_file_key}")

        return {
            'statusCode': 200,
            'body': 'New file created and uploaded successfully'
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Error creating or uploading the new file'
        }


def move_files(source_bucket, source_prefix, destination_bucket, destination_prefix):
    # Create an S3 client
    s3 = boto3.client('s3')
    
    # Get the current date in YYYYMMDD format
    current_date = datetime.now().strftime("%Y%m%d")

    # List all objects in the source path
    response = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)


    # Iterate through each object in the source path
    for obj in response.get('Contents', []):
        # Construct the source and destination object keys
        source_key = obj['Key']
        source_key_file = f"{source_key.split('/')[2]}"
        
        destination_key = source_key.replace(source_prefix, f"{destination_prefix}/{current_date}", 1)
        print(f"DESTINATIONKEY= {destination_key}")
        

        # Get the file content from S3
        response = s3.get_object(Bucket=source_bucket, Key=source_key)
        file_content = response['Body'].read()
        
        # Gzip the file content
        compressed_content = gzip.compress(file_content)
        
        # Upload the gzipped content to the new S3 key
        # if len(source_key_file) > 0 and source_key_file !=".keep":
        if source_key_file in required_files_list:
            s3.put_object(Body=compressed_content, Bucket=destination_bucket, Key=f"{destination_key}.gz", ContentEncoding='gzip')
        else: 
            continue


        # # Copy the object to the new location
        # s3.copy_object(
        #     Bucket=destination_bucket ,
        #     CopySource={'Bucket': source_bucket, 'Key': source_key},
        #     Key=destination_key
        # )
        if len(source_key_file) > 0 and source_key_file in required_files_list:
            # Delete the original object from the source path
            # os.remove(f"/{source_key}")
            s3.delete_object(Bucket=source_bucket, Key=source_key)
            print(f"Deleted: s3://{source_bucket}/{source_key}")

            print(f"Uploaded gzipped file to: s3://{destination_bucket}/{destination_key}")

        else:
            continue
    compressed_content = ""
    s3.put_object(Body=compressed_content, Bucket=destination_bucket, Key=f"{destination_prefix}/{current_date}/eor_{source_sys}.csv.gz", ContentEncoding='gzip')
    print("eor uploaded")

def lambda_handler(event, context):
    # Move files from source to destination
    move_files(source_bucket, source_prefix, destination_bucket, destination_prefix)
    # Update Copy script 
    update_copy_script()

    return {
        'statusCode': 200,
        'body': 'Files moved successfully!'
    }
