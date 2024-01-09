from aws_cdk import (
    # Duration,
    Stack,
    CfnParameter,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_s3_notifications as s3n,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    SecretValue,
    Duration,
    RemovalPolicy
)

import os
import json
from constructs import Construct

class MigrateExistingSFtpClientsToCloudInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a CfnParameter for the client acronym
        client_acromym = CfnParameter(self,"ClientAcronym",
                                      type="String",
                                      description="Enter the client acronym",)
        
        x_client_acronym = f"{client_acromym.value_as_string}"
        
        # Fill Out the below params
        MODULE = "lms"
        SOURCE_SYS = "oas"
        DESTINATION_BUCKET ="aapmr-dm-associationanalytics"
        SOURCE_BUCKET = "a2-ftp"
        customer = "aapmr"
        REQUIRED_FILES = "certifiedusers.csv;coursefeedbacks.csv;courses.csv;coursesintracks.csv;credits.csv;enrollments.csv;instructorrating.csv;learners.csv;performance.csv;tracks.csv"
        DEST_PREFIX	= f"data/{MODULE}_{SOURCE_SYS}"
        SOURCE_PREFIX = f"{x_client_acronym}_{SOURCE_SYS}"
        # SOURCE_PREFIX_PATH= f"{x_client_acronym}_{SOURCE_SYS}/toprocess"
        SOURCE_PREFIX_PATH= f"{x_client_acronym}_{MODULE}{SOURCE_SYS}/toprocess"
        
        # existing bucket
        bucket = s3.Bucket.from_bucket_attributes(self, "ExistingBucket",
        bucket_arn = f"arn:aws:s3:::{SOURCE_BUCKET}", 
        )
        
        # SKIP The "Directory Structure as the existing clients have this in place"
        
        
        # lambda role
        lambda_role = iam.Role(self, "LambdaSFTPRole",
                            #    removal_policy=RemovalPolicy.DESTROY,
                                role_name= f"{customer}_{MODULE}_{SOURCE_SYS}_SFTPLambdaRole",
                                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                                                  ],
                                )
        
        lambda_role.attach_inline_policy(
                            iam.Policy(self, f"{customer}-{MODULE}-{SOURCE_SYS}-lambda-SFTP-policy",
                    
                                        statements=[
                                            iam.PolicyStatement(
                                                effect=iam.Effect.ALLOW,
                                                actions=["s3:DeleteObject","s3:GetObject"],
                                                # resources=[f"arn:aws:s3:::{SOURCE_BUCKET}/{x_client_acronym}_{SOURCE_SYS}/toprocess/*"]
                                                resources=[f"arn:aws:s3:::{SOURCE_BUCKET}/{SOURCE_PREFIX_PATH}/*"]
                                    ),
                                            iam.PolicyStatement(
                                                effect=iam.Effect.ALLOW,
                                                actions=["s3:ListBucket"],
                                                resources=[f"arn:aws:s3:::{SOURCE_BUCKET}",
                                                            # f"arn:aws:s3:::{SOURCE_BUCKET}/{x_client_acronym}_{SOURCE_SYS}/toprocess*"]
                                                            f"arn:aws:s3:::{SOURCE_BUCKET}/{SOURCE_PREFIX}*"]
                                    ),
                                            iam.PolicyStatement(
                                                effect=iam.Effect.ALLOW,
                                                actions=["s3:PutObject"],
                                                # resources=[f"arn:aws:s3:::{DESTINATION_BUCKET}/data/{SOURCE_SYS}*"]
                                                resources=[f"arn:aws:s3:::{DESTINATION_BUCKET}/{DEST_PREFIX}*"]
                                    ),
                                            iam.PolicyStatement(
                                                effect=iam.Effect.ALLOW,
                                                actions=["s3:PutObject","s3:GetObject"],
                                                resources=[f"arn:aws:s3:::{DESTINATION_BUCKET}/scripts/*"]
                                    )
                                    ]
       ))
                                                   
        
        # Create lambda function
        sftp_lambda = lambda_.Function(self, "SFTPProcessFilesAuto",
                                       function_name=f"{x_client_acronym}-{MODULE}-{SOURCE_SYS}-SFTPProcessFilesAuto",
                                        runtime=lambda_.Runtime.PYTHON_3_10,
                                        handler="process_files.lambda_handler",
                                        code=lambda_.Code.from_asset(f"src/lambda/{SOURCE_SYS}"),
                                        role=lambda_role,
                                        timeout=Duration.seconds(300),
                                        memory_size=1024,
                                        environment={"DESTINATION_BUCKET": DESTINATION_BUCKET,
                                                     "DEST_PREFIX" : DEST_PREFIX,
                                                     "CUSTOMER": f"{x_client_acronym}",
                                                     "SOURCE_BUCKET": SOURCE_BUCKET,
                                                     "SOURCE_PREFIX": SOURCE_PREFIX_PATH,
                                                     "SOURCE_SYS": f"{MODULE}_{SOURCE_SYS}",
                                                     "REQUIRED_FILES": REQUIRED_FILES
                                                     },
                                        
                                       
        )
        # Event Bucket Notification fires the processing lambda
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                      s3n.LambdaDestination(sftp_lambda),
                                    s3.NotificationKeyFilter(prefix=f"{SOURCE_PREFIX_PATH}/"),
                                      s3.NotificationKeyFilter(suffix=".csv")
                                      )
        
        
        