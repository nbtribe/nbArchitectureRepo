import requests
import boto3
from botocore.exceptions import ClientError
import json
import sys
import polars as pl
import pyarrow
from flatten_json import flatten
from datetime import datetime, timedelta
from io import BytesIO, TextIOWrapper
import s3fs
import fsspec
import gzip





def get_ssm_param(param_name):
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(Name=param_name, WithDecryption=True)
    print(response["Parameter"]["Value"])
    data = response["Parameter"]["Value"]
    print(data)
    data = data.replace("'", '"')

    # print(type(data))
    response_json = json.loads(data)
    # print(response_json['access_token'])
    # print(response_json['expires_in'])
    # print(response_json['refresh_token'])

    return response_json


def getToken():
    url =f"{BASEURL}authenticate"

    payload = json.dumps({
        "username": USERNAME,
        "password": PASSWORD,
        "privateKey": API_KEY
    })
    headers = {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response = json.loads(response.text)

    return response

    
def upload_file_to_S3(df,filename):

        buffer = BytesIO()
        s3_key = f"{AWS_S3_DATA_FOLDER}{dateFolder}/{filename}.csv.gz"
        with gzip.GzipFile(mode="wb", fileobj=buffer) as zipped_file:
                df.write_csv(
                    TextIOWrapper(zipped_file, "utf8", newline=""),
                    separator=""
                )
        buffer2 = BytesIO(buffer.getvalue())
                
        s3_client = boto3.client("s3"
                                 ,
                            aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                            # region_name=AWS_REGION
                            
                            )
        s3_client.upload_fileobj(buffer2, BUCKET, s3_key)

        print(f"Uploading to {s3_key}")
        
        
        
def _GetUserIds():
    """Returns List of User Ids"""
    
    userIds = []
    url = f"{BASEURL}/users"
    
    payload = {}
    headers = {
        "x-api-key": API_KEY,
        "Authorization": f"Bearer {TOKEN}"
        # "Authorization": "Bearer XHOryQkplE3oxTiX6MxfTg==61ij0kKFlD0BF2IaXAylLKyj7jWgzU/Si5qyN9Cs7mxf0ukZlEQ0MmJk4RGuRAHF5mOZfOaupHZPxMI53+b+kEPlKkxs5bZsTCN1D1RluAWRAo01xVV0C5mlU19jt00X7oheI3AVQpyvTgN/SmBtcA=="
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    response = json.loads(response.text)
    print(response)
    for item in response:
        userIds.append(item["Id"])
    print(userIds)
    return userIds
        
def processRawData(rawData):
    rd_list = []
    processed_df = pl.DataFrame(None)
    
    for item in rawData:
        
        processedItem = flatten(item)
        print(processedItem)
        rd_list.append(processedItem)
    processed_df = pl.from_dicts(rd_list)
    for column in processed_df.columns:
        if processed_df[column].dtype in (pl.List,pl.Struct):
            processed_df = processed_df.drop(column)
    print(processed_df)
    return processed_df    


                
def getData(endpoint):
    url = f"{BASEURL}{endpoint}"

    payload = {}
    headers = {
        "x-api-key": API_KEY,
        "Authorization": f"Bearer {TOKEN}"
        # "Authorization": "Bearer XHOryQkplE3oxTiX6MxfTg==61ij0kKFlD0BF2IaXAylLKyj7jWgzU/Si5qyN9Cs7mxf0ukZlEQ0MmJk4RGuRAHF5mOZfOaupHZPxMI53+b+kEPlKkxs5bZsTCN1D1RluAWRAo01xVV0C5mlU19jt00X7oheI3AVQpyvTgN/SmBtcA=="
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    response = json.loads(response.text)
    print(response)
    return response

def getAttendances():
    pass


def getCertificates():
    result_df = pl.DataFrame(None)
    for id in user_id_list:
        temp_df = pl.DataFrame(None)
        url = f"{BASEURL}/users/{id}/certificates"
        payload = {}
        headers = {        "x-api-key": API_KEY,
        "Authorization": f"Bearer {TOKEN}"
        # "Authorization": "Bearer XHOryQkplE3oxTiX6MxfTg==61ij0kKFlD0BF2IaXAylLKyj7jWgzU/Si5qyN9Cs7mxf0ukZlEQ0MmJk4RGuRAHF5mOZfOaupHZPxMI53+b+kEPlKkxs5bZsTCN1D1RluAWRAo01xVV0C5mlU19jt00X7oheI3AVQpyvTgN/SmBtcA=="
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        response = json.loads(response.text)
        print(response)
        temp_df = processRawData(response)
        
        """These fields below were all mismatching on the dtype so we cast them to a utf-8"""
        # temp_df = temp_df.with_columns(
        #     pl.col().cast(pl.Utf8))

        result_df  = pl.concat([result_df,temp_df])
        print(result_df)
    upload_file_to_S3(result_df, "certificates")
        
        # return response
    

def getEnrollments():
    result_df = pl.DataFrame()
    for id in user_id_list:
        temp_df = pl.DataFrame(None)
        url = f"{BASEURL}/users/{id}/enrollments"
        payload = {}
        headers = {        "x-api-key": API_KEY,
        "Authorization": f"Bearer {TOKEN}"
        # "Authorization": "Bearer XHOryQkplE3oxTiX6MxfTg==61ij0kKFlD0BF2IaXAylLKyj7jWgzU/Si5qyN9Cs7mxf0ukZlEQ0MmJk4RGuRAHF5mOZfOaupHZPxMI53+b+kEPlKkxs5bZsTCN1D1RluAWRAo01xVV0C5mlU19jt00X7oheI3AVQpyvTgN/SmBtcA=="
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        response = json.loads(response.text)
        print(response)
        temp_df = processRawData(response)
        
        """These fields below were all mismatching on the dtype so we cast them to a utf-8"""
        temp_df = temp_df.with_columns(
            pl.col("DateCompleted","CourseCollectionId","DateExpires","AccessDate").cast(pl.Utf8))

        result_df  = pl.concat([result_df,temp_df])
        print(result_df)
    upload_file_to_S3(result_df, "enrollments")
        
        # return response
            




def getCountries():
    countryData = getData("countries")
    country_df = processRawData(countryData)
    upload_file_to_S3(country_df, "countries")

def getDepartments():
    departmentData = getData("departments")
    department_df = processRawData(departmentData)
    upload_file_to_S3(department_df, "departments")
    
# def getVenues():
#     venueData = getData("venues")
#     venue_df = processRawData(venueData)
#     upload_file_to_S3(venue_df, "venues")
    
def getCategories():
    categoryData = getData("categories")
    category_df = processRawData(categoryData)
    upload_file_to_S3(category_df, "categories")

def getCourses():
    courseData = getData("courses")
    course_df = processRawData(courseData)
    upload_file_to_S3(course_df, "courses")    
    
def getUsers():
    userId_list = []
    userData = getData("users")
    user_df = processRawData(userData)


    upload_file_to_S3(user_df, "users")
    # url = f"{BASEURL}/users"
    
    # payload = {}
    # headers = {
    #     "x-api-key": API_KEY,
    #     # "Authorization": f"Bearer {TOKEN}"
    #     "Authorization": "Bearer UPKshx3Ku5+qlZIuXV/LGQ==fePBL/nRUavsUNbfPi8hcQPpI1UMr8G5cpnbOlFrcKal+Do+AorZANuY/Z0v+3PZBHBsWsXgZgZO+ETz/zOaty/p8htXgT19Gnm+50+r3TW+Rysp0kBr0kEy1uS2glXkmGr84kpKX+HrmD6wE8bs0g=="
    # }

    # response = requests.request("GET", url, headers=headers, data=payload)
    

    # response = json.loads(response.text)
    # print(response)
    # sys.exit()
    # return response
    
    
def upload_eor_file_to_s3():
    # upload eor_file to trigger lambda function
    eor_df = pl.DataFrame(None)
    upload_file_to_S3(eor_df, "eor")
    
    
            
def update_copy_script():

    with fs.open(COPY_TEMPLATE) as f:
        script = f.read().decode('utf-8')
        

    script = script.format(date_folder = dateFolder)
    print(TODAY)
    print(script)

    with fs.open(COPY_SCRIPT, 'w') as f:
        f.write(script)
        
    upload_eor_file_to_s3()


if __name__ == "__main__":
    # If no organization acronym was provided, exit.
    if len(sys.argv) < 2:
        sys.exit("Client Acronym is missing")

    # client should be the second argument. First is the name of the script.
    # everything after that should be ignored.
    customer = sys.argv[1].upper()
    midnight = datetime.now()
    TODAY = midnight.strftime("%Y-%m-%d")
    ssm_values = get_ssm_param(f"/{customer.lower()}/Absorb_LMS/credentials")
    print(ssm_values)
    # sys.exit()
    API_KEY = ssm_values["Customer"][customer]["Absorb"]['x-api-key']
    BASEURL = ssm_values['baseurl']
    USERNAME = ssm_values["Customer"][customer]["Absorb"]['username']
    PASSWORD = ssm_values["Customer"][customer]["Absorb"]['password']
    AWS_ACCESS_KEY = ssm_values["Customer"][customer]["AWS"]['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = ssm_values["Customer"][customer]["AWS"]['AWS_SECRET_ACCESS_KEY'] 
    AWS_S3_DATA_FOLDER = ssm_values["Customer"][customer]["AWS"]['AWS_S3_DATA_FOLDER']
    BUCKET = ssm_values["Customer"][customer]["AWS"]['Bucket']
    COPY_TEMPLATE = ssm_values["Customer"][customer]["SQL"]['copy_template']
    COPY_SCRIPT = ssm_values["Customer"][customer]["SQL"]['copy_script']
    dateFolder = midnight.strftime("%Y%m%d")
    fs = s3fs.S3FileSystem(key=AWS_ACCESS_KEY, secret=AWS_SECRET_ACCESS_KEY)
    
    print('Application Starting')
    
    TOKEN = getToken()
    # print(TOKEN)
    user_id_list = _GetUserIds()
    # getCertificates()
    getEnrollments()
    # sys.exit()
    
    getUsers()
    getCourses()
    getCategories()
    getDepartments()
    getCountries()
    
    # getVenues()
    # print(TOKEN)
    # print(API_KEY)
    # print(BASEURL)
    # print(USERNAME)
    # print(PASSWORD)
    update_copy_script()
    print('Application ENding')