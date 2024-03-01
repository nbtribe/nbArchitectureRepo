import os
import json
import boto3
import botocore 
import botocore.session as bc
from botocore.client import Config
import sys
 
print('Loading function')
# s3 = boto3.client('s3')



def retrieve_sql_scripts_from_S3(s3_bucket,s3_key):
    s3 = boto3.resource('s3')
    # Download SQL file from S3
    print(s3_bucket)
    print(s3_key)
    
    try:
        obj = s3.Object(Bucket=s3_bucket, Key=s3_key)
        print(obj.key)
    
        sql_script = obj.get()['Body'].read().decode('utf-8')
        print(sql_script)
        return sql_script
    except Exception as e:
        print("Error downloading SQL file from S3:", e)
        return {
            'statusCode': 500,
            'body': "Error downloading SQL file from S3"
        }

def lambda_handler(event, context):

    config = event["querystring"]
    client_bucket = config["client_bucket"]
    deployment_buckt = config["deployment_bucket"]
    source_sys = config["source_system"]
    prefix = config["prefix"]
    source_sys = config["source_system"]
    customer = config["customer"]
    rs_connection = config["rs_connection"]
    file_path = f"integrations/{source_sys}/{customer}/{prefix}"

    s3 = boto3.client('s3')
    session = boto3.session.Session()
    region = session.region_name

    # Initializing Secret Manager's client    
    client = session.client(
        service_name='secretsmanager',
            region_name=region
        )

    get_secret_value_response = client.get_secret_value(
            SecretId=rs_connection
        )
    secret_arn=get_secret_value_response['ARN']

    secret = get_secret_value_response['SecretString']

    secret_json = json.loads(secret)

    cluster_id=secret_json['dbClusterIdentifier']

    # Initializing Botocore client
    bc_session = bc.get_session()

    session = boto3.Session(
            botocore_session=bc_session,
            region_name=region
        )

    # Initializing Redshift's client   
    config = Config(connect_timeout=5, read_timeout=5)
    client_redshift = session.client("redshift-data", config = config)

    # query_str = "create table public.lambda_func (id int);"
    sql_script = retrieve_sql_scripts_from_S3(s3_bucket=deployment_buckt, s3_key=f"integrations/{source_sys}/{customer}/sql/{customer}_{source_sys}_create_tables.sql")
    print(sql_script)
# sys.exit()
# try:
#     result = client_redshift.execute_statement(Database= 'dev', SecretArn= secret_arn, Sql= sql_script, ClusterIdentifier= cluster_id)
#     print("API successfully executed")
    
# except botocore.exceptions.ConnectionError as e:
#     client_redshift_1 = session.client("redshift-data", config = config)
#     result = client_redshift_1.execute_statement(Database= 'dev', SecretArn= secret_arn, Sql= sql_script, ClusterIdentifier= cluster_id)
#     print("API executed after reestablishing the connection")
#     return str(result)
    
# except Exception as e:
#     raise Exception(e)
    
# return str(result)