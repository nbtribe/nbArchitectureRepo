from datetime import datetime
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job


sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# set the bucket name where the input files were uploaded.
s3_bucket_name = "ag-tech-dev-raw-us-1-s3glueredshiftdatapipelinestack"
output_bucket = "ag-tech-dev-processed-us-1-s3glueredshiftdatapipelinestack"

input_loc = "s3://" + str(s3_bucket_name) + "/raw/977960622-2024-01-24T19_29_24"

# Add current date for partitioning
current_date = datetime.now().strftime("%Y-%m-%d")
output_loc = f"s3://{str(output_bucket)}/output/{current_date}/"

inputDF = glueContext.create_dynamic_frame_from_options(
    connection_type="s3",
    connection_options={
        "paths": [input_loc]
    },
    format="csv",
    format_options={
        "withHeader": True,
        "separator": ","
    })


outputDF = glueContext.write_dynamic_frame.from_options(
    frame=inputDF,
    connection_type="s3",
    connection_options={"path": output_loc
        },
    format="parquet")