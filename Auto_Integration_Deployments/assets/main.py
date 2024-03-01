import requests
import boto3
import botocore
from botocore.exceptions import ClientError
import json
import sys
import pandas as pd
# import pyarrow
from datetime import datetime, timedelta
from io import BytesIO, TextIOWrapper
# import s3fs
import gzip
import base64
import logging as logger
import time

def key_exists(bucket, key):
    s3 = boto3.client("s3")
    try:
        s3.head_object(Bucket=bucket, Key=key)
        print(f"Key: '{key}' found!")
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            print(f"Key: '{key}' does not exist!")
        else:
            print("Something else went wrong")
            raise

def update_copy_SCRIPT():
    s3 = boto3.resource('s3')
    # Check if obj_copy_script exists in s3 bucket. if not create it from the template
    if key_exists(BUCKET, COPY_SCRIPT):
        print("Copy Script exists")
    else:
        print("Copy Script does not exist")
        obj_copy_template = s3.Object(BUCKET, COPY_TEMPLATE_PATH)
        print(obj_copy_template.key)
        
        copy_template_contents = obj_copy_template.get()['Body'].read().decode('utf-8')
        print("Loading")
        obj_copy_script = s3.Object(BUCKET, COPY_SCRIPT_PATH)
        obj_copy_script.put(Body=copy_template_contents)
    
    
    print(copy_template_contents)
    copy_template_contents = copy_template_contents.replace("{client}", customer.lower()).replace(
        "{date_folder}", dateFolder)
        
    print(copy_template_contents)
    
    obj_copy_script.put(Body=copy_template_contents)
    print("Copy Script updated")

def get_ssm_param(param_name):
    client = boto3.client("ssm")
    response = client.get_parameter(Name=param_name, WithDecryption=True)
    response_json = json.loads(response["Parameter"]["Value"])
    return response_json

# def process_data(data):
#     data = flatten(data)
#     data = {k: v for k, v in data.items() if v}
#     return data

def get_base64(clientID,clientSecret):
    key =  base64.b64encode(f"{clientID}:{clientSecret}".encode("ascii")).decode("ascii")
    # print(key)
    return key
    
def getToken():
    url =f"{BASEURL}api/v1/oauth2/token.json"

    payload = "grant_type=client_credentials"
    headers = {
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "Authorization": f"Basic {AUTHKEY}"
}
    response = requests.request("POST", url, headers=headers, data=payload)
    response = json.loads(response.text)
    token = response["access_token"]

    return token

def backoff_API_requests():
    time.sleep(600)
def sendEORFile():
    eor_df = pd.DataFrame(None)
    upload_file_to_S3(eor_df, "eor", None)

    
    
def upload_file_to_S3(df,filename,req_columns):

        buffer = BytesIO()
        s3_key = f"{AWS_S3_DATA_FOLDER}{dateFolder}/{filename}.csv.gz"
        print(f"Uploading to {s3_key}")
        with gzip.GzipFile(mode="wb", fileobj=buffer) as zipped_file:
            df.to_csv(zipped_file, columns = df.columns, index=False,
                
                # TextIOWrapper(zipped_file, "utf8", newline=""),
                sep="", 
                )
        buffer2 = BytesIO(buffer.getvalue())
                
        s3_client = boto3.client("s3"
                                 ,
                            aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION
                            
                            )
        s3_client.upload_fileobj(buffer2, BUCKET, s3_key)

        print(f"Uploading to {s3_key}")
        
def get_cols(endpoint):
    field_list = scretVal["Customer"][customer]["Columns"][endpoint]
    fields = ",".join(field_list)
    return fields


def _getEventIDs(token):
    EVENT_FIELDS = get_cols("Events")

    url = f"{BASEURL}api/v1/events.json?fields={EVENT_FIELDS}&expand=&search=&page=&per-page=1000&sort"
    headers = {
    "Authorization": f"Bearer {token}"
    }

    response = requests.request("GET", url, headers=headers)
    response = json.loads(response.text)
    event_ids = [x["id"] for x in response["items"]]
    print(event_ids)
    
    return event_ids



def getEvents(token):
    EVENT_FIELDS = get_cols("Events")
    evt_df = pd.DataFrame()
    try:
        
        url = f"{BASEURL}api/v1/events.json?fields={EVENT_FIELDS}&expand=&search=&page=&per-page=1000&sort"
        headers = {
        "Authorization": f"Bearer {token}"    
        }
        parameters = {
            "fields": EVENT_FIELDS,
            "expand": "",
            "search": "",
            "page": "",
            "per-page": "1000",
            "sort": ""}
            
        
        response = requests.get(url, params=parameters, headers=headers)   
        response_json = json.loads(response.text)
        
        # print(response_json['items'])
        print(response)

            
        # if response_json['items']:
        if 'items' in response_json:
            evt_df = pd.DataFrame(response_json['items'])

        else:
            print(f"No events found") 
            logger.info(f"No events found")
            
        upload_file_to_S3(evt_df, "events", EVENT_FIELDS)
    except Exception as e:
        print(e)
        logger.info(e)
        # Handle token expiration
        print("Sleeping for 10 min....")
        backoff_API_requests()
        print("Resume.....")
        # Refresh token
        
        token = getToken()
        

def getEventRegistrations(token, EVENT_IDS):
    EVENT_REG_FIELDS = get_cols("Event_Registrations")  # Assuming get_cols function is defined elsewhere
    reg_df = pd.DataFrame()

    for event_id in EVENT_IDS:
        try:
            print(f"Fetching registrations for event ID: {event_id}")
            logger.info(f"Fetching registrations for event ID: {event_id}")

            url = f"{BASEURL}api/v1/registrants.json"
            headers = {"Authorization": f"Bearer {token}"}
            parameters = {
                "event_id": event_id,
                "fields": EVENT_REG_FIELDS,
                "per-page": "1000",
                "expand": "",
                "search": "",
                "page": "",
            }

            response = requests.get(url, params=parameters, headers=headers)
            response.raise_for_status()

            response_json = response.json()
            if 'items' in response_json:
                df = pd.DataFrame(response_json['items'])
                print(df)
                reg_df = pd.concat([reg_df, df])
                print(f"Registrations found for event {event_id}")
                logger.info(f"Registrations found for event {event_id}")
            else:
                print(f"No registrations found for event {event_id}")
                logger.info(f"No registrations found for event {event_id}")



        except requests.exceptions.HTTPError as http_err:
            print((f"HTTP error occurred: {http_err}"))
            logger.error(f"HTTP error occurred: {http_err}")
            if response.status_code == 401:
                token = getToken()
                continue
            if response.status_code == 404:
                print("API endpoint not found. Exiting...")
                logger.error("API endpoint not found. Exiting...")
                sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            logger.info(f"An error occurred: {e}")
            print("Sleeping for 10 minutes...")
            time.sleep(600)
            print("Resuming...")
            token = getToken()  # Refresh token
            continue

    # Upload to S3
    upload_file_to_S3(reg_df, "event_registrations", EVENT_REG_FIELDS)
    print("Data uploaded to S3")

    # Sleeping for 10 minutes
    print("Sleeping for 10 minutes...")
    time.sleep(600)
    print("Resume...")
        
def getRegistrationLineItems(token,EVENT_IDS):
    
    
    EVENTREG_LINE_ITEMS = get_cols("Registration_Line_Items")
    reg_line_items_df = pd.DataFrame()
    for event_id in EVENT_IDS:
        try:
            print(f"Fetching registration line items for event ID: {event_id}")
            logger.info(f"Fetching registrations line items for event ID: {event_id}")

            url = f"{BASEURL}api/v1/registrant-line-items.json"
            headers = {"Authorization": f"Bearer {token}"}
            parameters = {
                "event_id": event_id,
                "fields": EVENTREG_LINE_ITEMS,
                "per-page": "1000",
                "expand": "",
                "search": "",
                "page": "",
            }

            response = requests.get(url, params=parameters, headers=headers)
            response.raise_for_status()

            response_json = response.json()
            if 'items' in response_json:
                df = pd.DataFrame(response_json['items'])
                print(df)
                reg_line_items_df = pd.concat([reg_line_items_df, df])
                print(f"registrations line items found for event {event_id}")
                logger.info(f"registrations line items found for event {event_id}")
            else:
                print(f"No registrations line items found for event {event_id}")
                logger.info(f"No registrations line items found for event {event_id}")



        except requests.exceptions.HTTPError as http_err:
            print((f"HTTP error occurred: {http_err}"))
            logger.error(f"HTTP error occurred: {http_err}")
            if response.status_code == 401:
                token = getToken()
                continue
            if response.status_code == 404:
                print("API endpoint not found. Exiting...")
                logger.error("API endpoint not found. Exiting...")
                sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            logger.info(f"An error occurred: {e}")
            print("Sleeping for 10 minutes...")
            time.sleep(600)
            print("Resuming...")
            token = getToken()  # Refresh token
            continue

    # Upload to S3
    upload_file_to_S3(reg_line_items_df, "event_registration_line_items", EVENTREG_LINE_ITEMS)
    print("Data uploaded to S3")

    # Sleeping for 10 minutes
    print("Sleeping for 10 minutes...")
    time.sleep(600)
    print("Resume...")

    
def getRegistrantTypes(token,EVENT_IDS):
    REGISTRANT_TYPES = get_cols("Registrant_Types")
    reg_types_df = pd.DataFrame()
    for event_id in EVENT_IDS:

        df = pd.DataFrame(None)

        url = f"{BASEURL}api/v1/reg-types.json"
        headers = {
        "Authorization": f"Bearer {token}"
        }
        parameters = {
            "event_id": event_id,
            "fields" : REGISTRANT_TYPES,
            "expand": "",
            "search": "",
            "page": "",
            "per-page": "1000",
            "sort": ""}
        
        print(url)
        print(parameters)
        print(headers)
        response = requests.get(url, params=parameters, headers=headers)

        response_json = json.loads(response.text)

        # print(response_json['items'])
        # if response_json['items']:
        if 'items' in response_json:
            df = pd.DataFrame(response_json['items'])
            reg_types_df = pd.concat([reg_types_df, df])
            print(reg_types_df)

        else:
            print(f"No registrant types for event {event_id}")
            logger.info(f"No registrant types for event {event_id}")

    upload_file_to_S3(reg_types_df, "registrant_types", REGISTRANT_TYPES)
    print("Sleeping for 10 min....")
    backoff_API_requests()
    print("Resume.....")
    
    
def getEventQuestions(token, EVENT_IDS):
    EVENT_QUESTIONS = get_cols("Event_Questions")
    event_questions_df = pd.DataFrame()
    for event_id in EVENT_IDS:
        
        try:
            print(f"Fetching Event_Questions for event ID: {event_id}")
            logger.info(f"Fetching Event_Questionss for event ID: {event_id}")

            url = f"{BASEURL}api/v1/event-questions.json"
            headers = {"Authorization": f"Bearer {token}"}
            parameters = {
                "event_id": event_id,
                "fields": EVENT_QUESTIONS,
                "per-page": "1000",
                "expand": "",
                "search": "",
                "page": "",
            }

            response = requests.get(url, params=parameters, headers=headers)
            response.raise_for_status()

            response_json = response.json()
            if 'items' in response_json:
                df = pd.DataFrame(response_json['items'])
                print(df)
                event_questions_df = pd.concat([event_questions_df, df])
                print(f"Event_Questions found for event {event_id}")
                logger.info(f"Event_Questions found for event {event_id}")
            else:
                print(f"No Event_Questions found for event {event_id}")
                logger.info(f"No Event_Questions found for event {event_id}")



        except requests.exceptions.HTTPError as http_err:
            print((f"HTTP error occurred: {http_err}"))
            logger.error(f"HTTP error occurred: {http_err}")
            if response.status_code == 401:
                token = getToken()
                continue
            if response.status_code == 404:
                print("API endpoint not found. Exiting...")
                logger.error("API endpoint not found. Exiting...")
                sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            logger.info(f"An error occurred: {e}")
            print("Sleeping for 10 minutes...")
            time.sleep(600)
            print("Resuming...")
            token = getToken()  # Refresh token
            continue

    # Upload to S3
    upload_file_to_S3(event_questions_df, "event_questions", EVENT_QUESTIONS)
    print("Data uploaded to S3")

    # Sleeping for 10 minutes
    print("Sleeping for 10 minutes...")
    time.sleep(600)
    print("Resume...")
    
    
def getSessions(token, EVENT_IDS):
        SESSIONS = get_cols("Sessions")
        sessions_df = pd.DataFrame()
        for event_id in EVENT_IDS:
            
            try:
                print(f"Fetching Sessions for event ID: {event_id}")
                logger.info(f"Fetching Sessions for event ID: {event_id}")

                url = f"{BASEURL}api/v1/sessions.json"
                headers = {"Authorization": f"Bearer {token}"}
                parameters = {
                    "event_id": event_id,
                    "fields": SESSIONS,
                    "per-page": "1000",
                    "expand": "",
                    "search": "",
                    "page": "",
                }

                response = requests.get(url, params=parameters, headers=headers)
                response.raise_for_status()

                response_json = response.json()
                if 'items' in response_json:
                    df = pd.DataFrame(response_json['items'])
                    print(df)
                    sessions_df = pd.concat([sessions_df, df])
                    print(f"Sessions found for event {event_id}")
                    logger.info(f"Sessions found for event {event_id}")
                else:
                    print(f"No Sessions found for event {event_id}")
                    logger.info(f"No Sessions found for event {event_id}")



            except requests.exceptions.HTTPError as http_err:
                print((f"HTTP error occurred: {http_err}"))
                logger.error(f"HTTP error occurred: {http_err}")
                if response.status_code == 401:
                    token = getToken()
                    continue
                if response.status_code == 404:
                    print("API endpoint not found. Exiting...")
                    logger.error("API endpoint not found. Exiting...")
                    sys.exit(1)
            except Exception as e:
                print(f"An error occurred: {e}")
                logger.info(f"An error occurred: {e}")
                print("Sleeping for 10 minutes...")
                time.sleep(600)
                print("Resuming...")
                token = getToken()  # Refresh token
                continue

        # Upload to S3
        upload_file_to_S3(sessions_df, "sessions", SESSIONS)
        print("Data uploaded to S3")

        
if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        sys.exit("Client Acronym is missing")
        
    customer = sys.argv[1].upper()
    
    scretVal = get_ssm_param(f"/{customer}/swoogo/credentials")

    print("Application Starting")
    TODAY = datetime.today().strftime("%Y%m%d")

    BASEURL = scretVal["Customer"][customer]["API"]["baseurl"]
    consumerKey = scretVal["Customer"][customer]["API"]["consumerKey"]
    consumerSecret = scretVal["Customer"][customer]["API"]["consumerSecret"]
    AWS_ACCESS_KEY =  scretVal["Customer"][customer]["AWS"]["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY =   scretVal["Customer"][customer]["AWS"]["AWS_SECRET_ACCESS_KEY"]
    AWS_REGION = scretVal["Customer"][customer]["AWS"]["Region"]
    BUCKET = scretVal["Customer"][customer]["AWS"]["Bucket"]
    AWS_S3_DATA_FOLDER = scretVal["Customer"][customer]["AWS"]["AWS_S3_DATA_FOLDER"]
    AUTHKEY = get_base64(consumerKey,consumerSecret)
    dateFolder = datetime.today().strftime("%Y%m%d")
    COPY_SCRIPT = scretVal["Customer"][customer]["SQL"]["copy_script"]
    COPY_template = scretVal["Customer"][customer]["SQL"]["copy_template"]
    COPY_SCRIPT_PATH = scretVal["Customer"][customer]["AWS"]["copy_script_key"]
    COPY_TEMPLATE_PATH = scretVal["Customer"][customer]["AWS"]["copy_template_key"]




    # token = getToken()
    # EVENT_IDS = _getEventIDs(token)
    # getEvents(token)
    # getEventRegistrations(token, EVENT_IDS)
    # getRegistrantTypes(token, EVENT_IDS)
    # getRegistrationLineItems(token,EVENT_IDS)
    # getEventQuestions(token, EVENT_IDS)
    # getSessions(token, EVENT_IDS)
    update_copy_SCRIPT()
    sendEORFile()
    
    print("Application Ending")
    