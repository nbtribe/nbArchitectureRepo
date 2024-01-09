import boto3
import json
from botocore.exceptions import ClientError
import psycopg2 as pg2
from datetime import date, timedelta, datetime, time
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2.extras
import pymsteams
import pandas as pd
import sys

print('Loading function')
s3 = boto3.client('s3')


def get_secret(secret_name, region='us-east-1'):

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e
    secret = json.loads(get_secret_value_response['SecretString'])
    return secret

def lambda_handler(event, context):
    msg = get_records()
    send_message(msg)


def get_records():
    # http://a2etlmonitor.s3-website-us-east-1.amazonaws.com

    print('start MTA DAILY etl_monitor_send_teams_message.py')

    # database connection info
    secret = get_secret('rs-a2dbowner-assocanalytics')
    RS_HOST = secret['host']
    RS_PORT = secret['port']
    RS_DB = 'admin'
    RS_USER = secret['username']
    RS_PWD = secret['password']

    connection = pg2.connect(
        dbname=RS_DB, user=RS_USER, host=RS_HOST, port=RS_PORT, password=RS_PWD)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT customer, source, lrd, status, info, airflow"
                             " FROM admin.vw_etl_current_status"
                             " WHERE source = 'MTA Build'"
                             " AND status <> 'success';")
    rows = cursor.fetchall()
    print(rows)
    columns = ['Customer', 'Source', 'Last Refresh',
                 'Status', 'Info', 'Airflow']

    etl_df = pd.DataFrame()
    print(etl_df)
    
    
    for row in rows:
        data = {column.lower(): value for column, value in zip(columns, row)} 
        etl_df = etl_df.append(data, ignore_index=True)

    if etl_df.empty:
        etl_df = pd.DataFrame(columns=columns)
        etl_df = etl_df.to_html(escape=False, render_links=True,index=False)
    else:
        etl_df['airflow']=etl_df['airflow'].apply(make_hyperlink)
        etl_df['last refresh'] = etl_df['last refresh'].dt.round('min')
        etl_df = etl_df.to_html(escape=False, render_links=True,index=False)
   
    return etl_df

def make_hyperlink(val):
    link_str = "LINK"
    return f'<a target="_blank" href="{val}">{link_str}</a>'

# send message to teams
def send_message(msg):
    # Teams webhook URL
    webhook_url = "[MS_Teams_WebHook]"

    # Create a new message
    message = pymsteams.connectorcard(webhook_url)

    # Add text to the message
    message.text(msg)

    # Send the message to Teams
    message.send()
    
    
# main()
print('End MTA DAILY etl_monitor_send_teams_message.py')