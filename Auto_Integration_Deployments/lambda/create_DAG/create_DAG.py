
import boto3
import sys

# CUSTOMER  = "swana"
# RS_CONNECTION = "assocanalytics5"
# DATABASE = "DB000"
# SOURCE_SYSTEM = "lms_swgo"
# INTEGRATION = "Swoogo"
# BUCKET = "swana-dm-associationanalytics"

def create_DAG(config):

    CUSTOMER = config["customer"]
    BUCKET = config["client_bucket"]
    SOURCE_SYSTEM = config["source_system"]
    RS_CONNECTION = config["rs_connection"]
    DATABASE = config["database"]
    INTEGRATION = config["integration"]
    CLUSTER = RS_CONNECTION.split("-")[2]

    dag_template = f"""
from airflow import DAG
from operators.A2Postgres import A2PostgresOperator
from airflow.operators.python_operator import PythonOperator
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator
from airflow.providers.amazon.aws.operators.sns import SnsPublishOperator
import os
import time
from datetime import timedelta, datetime
from airflow.utils.dates import days_ago

import pendulum



local_tz = pendulum.timezone('America/New_York')

#Checks todays date folder for EOR file
def check_eor_exists(bucket, datafolder, filename):
    import boto3
    import botocore
    print(datetime.now())
    today = (datetime.now()).strftime('%Y%m%d') #Subtract 5 hours as server is in UTC
    s3 = boto3.resource('s3')
    try:
        s3.Object(bucket, datafolder+today+'/'+filename).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            raise Exception ('EOR Not Found')
        else:
            raise Exception('EOR Not found - could not look for file')
    else:
        return 'EOR Found'
DEFAULT_ARGS = {{
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False
}}
DAG_ID = os.path.basename(__file__).replace('.py', '')
with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    dagrun_timeout=timedelta(hours=4),
    start_date=datetime(2023, 7, 5, 1 , 0, tzinfo=local_tz), 
    schedule_interval='0 1 * * *' ,
    tags = ['{CUSTOMER.upper()}','{CLUSTER}','{DATABASE}','{SOURCE_SYSTEM}','122']
) as dag:


    connection = 'a2-{RS_CONNECTION}_conn' 
    dbnumber = '{DATABASE}' 
    bucket = '{BUCKET}'
    script_1_location = 'scripts/{CUSTOMER}_{SOURCE_SYSTEM}_copy_statement.sql'
    script_2_location = 'scripts/{CUSTOMER}_{SOURCE_SYSTEM}_upsert.sql'   
    success_sns_message = '{CUSTOMER.upper()} {SOURCE_SYSTEM.upper().replace('_',' ')} ETL Success'
    fail_sns_message = '{CUSTOMER.upper()} {SOURCE_SYSTEM.upper().replace('_',' ')} ETL Fail'
    success_sns_arn = 'arn:aws:sns:us-east-1:009885916296:ETLSuccessCommon'
    fail_sns_arn = 'arn:aws:sns:us-east-1:009885916296:ETLFailCommon'



    run_ecs_task = EcsRunTaskOperator(
        task_id='ecs_operator_task',
        dag=dag,
        cluster='integration-cluster',
        task_definition='{INTEGRATION}',
        launch_type='FARGATE',
        overrides={{
            'containerOverrides': [
                {{
                    'name': '{INTEGRATION}',
                    'command': ['{CUSTOMER.upper()}'],
                }},
            ],
        }},
        network_configuration={{
            'awsvpcConfiguration': {{
                'subnets': ['subnet-78a1c374', 'subnet-1f3b2c35', 'subnet-1f0a757a'],
                'assignPublicIp': 'ENABLED',
                'securityGroups': ['sg-ac5689d6'],
            }}
        }},
    )

        check_eor = PythonOperator(
        task_id = 'check_eor',
        python_callable = check_eor_exists,
        op_args=['{BUCKET}', 'data/{SOURCE_SYSTEM}/', 'eor.csv.gz'],
        
    
    )

        script_1 = A2PostgresOperator(
        postgres_conn_id = connection,
        database = dbnumber,
        task_id='script_1',
        bucket = bucket,
        script_location = script_1_location,
        retries =1,
        retry_delay = timedelta(minutes=1),
    )

    script_2 = A2PostgresOperator(
        postgres_conn_id = connection,
        database = dbnumber,
        task_id='script_2',
        bucket = bucket,
        script_location = script_2_location,
        retries =1,
        retry_delay = timedelta(minutes=1),
    )

    sns_pass = SnsPublishOperator(
        task_id='sns_pass',
        target_arn=success_sns_arn,
        message=success_sns_message, 
        subject=success_sns_message,
        retries =1
    )

    sns_fail = SnsPublishOperator(
        task_id='sns_fail',
        target_arn=fail_sns_arn,
        message=fail_sns_message, 
        subject=fail_sns_message,
        retries =1,
        trigger_rule='one_failed'
    )

    run_ecs_task >> check_eor >> script_1 >> script_2 >> sns_pass >> sns_fail
                """

    print(dag_template)
    return dag_template

def lambda_handler(event, context):
    config = event["querystring"]
    deployment_buckt = config["deployment_bucket"]
    prefix = config["prefix"]
    SOURCE_SYSTEM = config["source_system"]
    CUSTOMER = config["customer"]
    RS_CONNECTION = config["rs_connection"]
    BUCKET = config["client_bucket"]
    dag = create_DAG(config)
    

    # S3 bucket path

    file_key = f'dags/{CUSTOMER.upper()}/{CUSTOMER}_{SOURCE_SYSTEM}_etl.py'
    
    # Create S3 client
    s3 = boto3.client('s3')
    
    # Upload the DAG to S3
    try:
        response = s3.put_object(
            Bucket=BUCKET,
            Key=file_key,
            Body=dag.encode('utf-8')  # Convert string to bytes
        )
        print("DAG file uploaded successfully!")
        return {
            'statusCode': 200,
            'body': 'DAG file uploaded successfully!'
        }
    except Exception as e:
        print(f"Error uploading DAG file to S3: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error uploading DAG file to S3: {str(e)}"
        }