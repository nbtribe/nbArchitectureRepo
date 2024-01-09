import boto3
import os
from datetime import datetime 
import sys
import json
import io
import gzip

# OASIS SFTP LAMBDA
# Get the current date in YYYYMMDD format
current_date = datetime.now().strftime("%Y%m%d")
source_bucket = os.environ["SOURCE_BUCKET"]
destination_bucket = os.environ["DESTINATION_BUCKET"]
destination_prefix = os.environ["DEST_PREFIX"]
source_prefix = os.environ["SOURCE_PREFIX"]
customer = os.environ["CUSTOMER"]
source_sys = os.environ["SOURCE_SYS"]
required_files = os.environ["REQUIRED_FILES"]
required_files_list = list(required_files.split(";"))
s3 = boto3.client('s3')
print(required_files_list) 

def check_required_files():
    # Get the list of files in the source bucket
    present_file_list =[]
    response = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)["Contents"]
    
    for key in response:
        
        filename = os.path.basename(key["Key"]) 
        filename = clean_filename(filename)
        print(filename)
        if filename != ".csv":
            present_file_list.append(filename)
        else:
            pass
            

    # sys.exit()
    
    present_file_list.sort()
    required_files_list.sort()
    if present_file_list != required_files_list:
        print("FALSE")
        return False
    else:
        print("TRUE")
        return True
    # # Check if all required files are present
    # for filename in required_files_list:
    #     # print(f'file = {file}')
    #     # file = clean_filename(file)
    #     if filename not in files:
    #         print(f"All files not found in source bucket or extra files found")
    #         return False
    # priint("TRUE")
    # return True
    
def update_copy_script():
    template_key = f'{customer.lower()}_{source_sys}_copy_template.sql'
    scripts_folder = 'scripts/'
    print(f"template_key = {template_key}")


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
        
 # Oasis specific- they send a file like CertifiedUsers - 03-29-2023.csv
def clean_filename(filename):
    # Replace all non-alphanumeric characters with underscores
    filename = f"{filename.split('-')[0].strip().lower()}.csv"
    return filename

def move_files(source_bucket, source_prefix, destination_bucket, destination_prefix):

    # List all objects in the source path
    response = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)


    # Iterate through each object in the source path
    for obj in response.get('Contents', []):
        # Construct the source and destination object keys
        source_key = obj['Key']
        print(f"THIS IS THE SOURCE KEY {source_key}")
        source_key_file = f"{source_key.split('/')[2]}"
        print(source_key_file)
        
        # Oasis specific- they send a file like CertifiedUsers - 03-29-2023.csv
        
        source_key_file = clean_filename(source_key_file)
        
        # destination_key = source_key.replace(source_prefix, f"{destination_prefix}/{current_date}", 1)
        destination_key = source_key.replace(source_key, f"{destination_prefix}/{current_date}/{source_key_file}",1)
        print(f"DESTINATIONKEY= {destination_key}")
        

        # Get the file content from S3
        response = s3.get_object(Bucket=source_bucket, Key=source_key)
        file_content = response['Body'].read()
        
        # Gzip the file content
        compressed_content = gzip.compress(file_content)
        
        # Upload the gzipped content to the new S3 key
        # if len(source_key_file) > 0 and source_key_file !=".keep":
        if source_key_file in required_files_list:
            print(f"THIS is sourceKEYFILE {source_key_file}")
            s3.put_object(Body=compressed_content, Bucket=destination_bucket, Key=f"{destination_key}.gz", ContentEncoding='gzip')
            # s3.put_object(Body=compressed_content, Bucket=destination_bucket, Key=f"{destination_key}{source_key_file}.gz", ContentEncoding='gzip')
        else: 
            continue



        if len(source_key_file) > 0 and source_key_file in required_files_list:
            # Delete the original object from the source path
            # os.remove(f"/{source_key}")
            s3.delete_object(Bucket=source_bucket, Key=source_key)
            print(f"Deleted: s3://{source_bucket}/{source_key}")

            print(f"Uploaded gzipped file to: s3://{destination_bucket}/{destination_key}")

        else:
            continue
    
    # s3.put_object(Body=compressed_content, Bucket=destination_bucket, Key=f"{destination_prefix}/{current_date}/eor_{source_sys}.csv.gz", ContentEncoding='gzip')
    # print("eor uploaded")
def upload_eor():
    compressed_content = ""
    s3.put_object(Body=compressed_content, Bucket=destination_bucket, Key=f"{destination_prefix}/{current_date}/eor_oasislms.csv.gz", ContentEncoding='gzip')
    print("eor uploaded")
    
def lambda_handler(event, context):
    
    files_present = check_required_files()
    if files_present is False:
        return {
            'statusCode': 500,
            'body': 'ALL Required files not found in source bucket'
        }
    else:
        # Move files from source to destination
        move_files(source_bucket, source_prefix, destination_bucket, destination_prefix)
        # Upload EOR
        upload_eor()
        # Update Copy script 
        update_copy_script()


        return {
            'statusCode': 200,
            'body': 'Files moved successfully!'
        }
