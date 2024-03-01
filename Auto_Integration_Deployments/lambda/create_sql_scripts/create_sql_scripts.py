import boto3
from botocore.exceptions import ClientError
import os
import json
# import ast
import csv
import sys

longest, headers, type_list, result_files = [], [], [], []
formatted_file = ''
table_name = ''
f = ''
reader = csv.reader(formatted_file)

special_characters = '-\'/!@#$%^&*()+=-{[}]~`?|:;.,"<>\n\t '
# client_buckt = os.environ["CLIENT_BUCKET"]
# deployment_bucket = os.environ["DEPLOYMENT_BUCKET"]
# source_sys = os.environ["SOURCE_SYSTEM"]
# prefix = os.environ["PREFIX"]
# # iam_role = os.environ["IAM_ROLE"]
# customer = os.environ["CUSTOMER"]
# file_path = f"integrations/{source_sys}/{customer}/{prefix}"

# a2-integration-deployments
# integrations/
# lms_acg/
# acme/
# integration_sample_files/


def upload_to_s3(content, bucket_name, file_key):
    """
    Uploads content to an S3 bucket.
    """
    s3 = boto3.client('s3')
    try:
        if isinstance(content, str):
            content = content.encode('utf-8')  # Convert to bytes if content is string
        s3.put_object(Body=content, Bucket=bucket_name, Key=file_key)
        print(f"Content uploaded to S3://{bucket_name}/{file_key}")
    except Exception as e:
        print(f"Error uploading content to S3: {e}")



def create_table_sql(schema, table_name, s3_bucket, s3_prefix, config):
    s3 = boto3.client('s3')
    result_files = []
    create_statements = ""
    copy_statements = ""
    source_sys = config["source_system"]
    customer = config["customer"]
    client_buckt = config["client_bucket"]
    deployment_bucket = config["deployment_bucket"]
    file_path = f"integrations/{source_sys}/{customer}/{s3_prefix}"
    
    
    # List objects in the S3 bucket
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=s3_prefix)
    for obj in response.get('Contents', []):
        result_files.append(obj['Key'])
    
    for rf in result_files:
        headers = []
        table_name = os.path.basename(rf).split(".")[0]
        if len(table_name)==0:
            continue
        print(f"Performing DB functions on file {table_name}")
        
        # Download CSV file from S3
        obj = s3.get_object(Bucket=s3_bucket, Key=rf)
        reader = csv.reader(obj['Body'].read().decode('utf-8').splitlines())
        
        for row in reader:
            if len(headers) == 0:
                headers = row
                for col in row:
                    #print(' Col = {}'.format(col))
                    longest.append(len(col)+200)
                    type_list.append('')
            else:
                for i in range(len(row)):
                    # NA is the csv null value
                    if type_list[i] == 'varchar' or row[i] == 'NA':
                        pass
                    else:
                        pass
                if len(row[i]) > longest[i]:
                    longest[i] = len(row[i])
        
           # Construct CREATE TABLE statement
        statement = f'CREATE TABLE IF NOT EXISTS {schema}.{source_sys}_{table_name} ('
        for i, header in enumerate(headers):
            statement += f'\n{header.lower()} varchar({str(longest[i])}) encode lzo,'
        statement = statement[:-1] + ") \n DISTSTYLE ALL;\n\n"
        print(statement)
        create_statements = create_statements + statement + "\n"
        
        


        
        # Construct COPY statement to load data from S3
        sql_st = f"TRUNCATE TABLE {schema}.{source_sys}_{table_name};\n COPY {schema}.{source_sys}_{table_name} ("
        for header in headers:
            sql_st += f"\n{header.lower()},"
        sql_st = sql_st[:-1] + f") from 's3://{client_buckt}/data/{source_sys}/{{dateFolder}}/{os.path.basename(rf)}.gz' IAM_ROLE '{os.environ['IAM_ROLE']}' ignoreheader as 1 gzip DELIMITER AS '' CSV QUOTE '\"' timeformat'MM/DD/YYYY HH:MI:SS AM' TRIMBLANKS TRUNCATECOLUMNS ACCEPTINVCHARS  AS ' ';\n\n"
        print(sql_st)
        copy_statements = copy_statements + sql_st + "\n"
        
    
        
    """upload CREATE TABLES"""
    upload_to_s3(create_statements, deployment_bucket, f"integrations/{source_sys}/{customer}/sql/{customer}_{source_sys}_create_tables.sql")
    """upload COPY_TEMPLATE"""
    upload_to_s3(copy_statements, client_buckt,f"scripts/{customer}_{source_sys}_copy_template.sql")
    """upload UPSERT SCRIPT"""
    upload_to_s3(f"--{customer}_{source_sys}_upsert.sql", client_buckt,f"scripts/{customer}_{source_sys}_upsert.sql")


# def make_create_scripts(s3_location):
#     s3 = boto3.client('s3')

#     try:
#         # List objects in the specified bucket
#         response = s3.list_objects_v2(
#             Bucket=bucket_name
#         )

#         # Iterate over each object in the bucket
#         for obj in response.get('Contents', []):
#             print('Object Key:', obj['Key'])
#             # You can add more operations here, such as downloading or processing the object

#     except Exception as e:
#         print(f"An error occurred: {e}")


def lambda_handler(event,context):
    print(event)
    input_data = event.get('data')
    print(input_data)
    config = event["querystring"]
    deployment_buckt = config["deployment_bucket"]
    source_sys = config["source_system"]
    prefix = config["prefix"]
    source_sys = config["source_system"]
    customer = config["customer"]
    file_path = f"integrations/{source_sys}/{customer}/{prefix}"
    create_table_sql("source", table_name, deployment_buckt, file_path, config)
    return True



