from aws_cdk import (
    Duration,
    RemovalPolicy,
    CfnOutput,
    CfnParameter,
    Stack,
    aws_sqs as sqs,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_s3_notifications as s3_notifications,
    aws_glue as glue,
    aws_iam as iam,
    aws_redshift as redshift,
    aws_secretsmanager as aws_secretsmanager,
    aws_lambda as _lambda,
    # aws_lambda_python_alpha as alambda_,
    aws_lambda_event_sources as event_sources,
    aws_appflow as appflow
)
from constructs import Construct

class GoogleAnalyticsEtlAppFlowGlueStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Manually create Appflow that will serve as out extract piece of the project

        #Create  S3 bucket for raw data
        bucket_raw_data  = s3.Bucket(
            self, f"S3Bucket",
            bucket_name=f"ag-tech-dev-raw-us-1-{construct_id.lower()}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
        # Add bucket policy for appflow ingestion location
        bucket_raw_data.add_to_resource_policy(iam.PolicyStatement(
            actions=["s3:PutObject",
                "s3:AbortMultipartUpload",
                "s3:ListMultipartUploadParts",
                "s3:ListBucketMultipartUploads",
                "s3:GetBucketAcl",
                "s3:PutObjectAcl"],
            resources=[bucket_raw_data.bucket_arn,
                    bucket_raw_data.bucket_arn + "/*"],
            sid="AllowAppFlowDestinationActions",
            effect=iam.Effect.ALLOW,
            principals=[iam.ServicePrincipal("appflow.amazonaws.com")],
            conditions={
                "StringEquals": {
                    "aws:SourceAccount": self.account
                    }
            }
        )

        )
        # Create S3 bucket for processed data
        bucket_processed_data = s3.Bucket(
            self, f"S3BucketProcessed",
            bucket_name=f"ag-tech-dev-processed-us-1-{construct_id.lower()}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Create S3 bucket for glue Assets
        glue_assets_bucket = s3.Bucket(self,
                                       "GlueAssetsBucket",
                                       bucket_name=f"ag-tech-dev-glue-assets-us-1-{construct_id.lower()}",
                                       versioned=True,
                                       removal_policy=RemovalPolicy.DESTROY,
                                       auto_delete_objects=True,
                                       block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )



        # Glue Job Execution Role
        glue_job_role = iam.Role(
            self, "GlueJobRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")],

        )

        # asset to sync scripts with S3 Bucket
        asset = s3_deployment.Source.asset("./glue_jobs")

        # Sync scripts
        s3_deployment.BucketDeployment(self, "DeployGlue Scrpts",
                                        sources=[s3_deployment.Source.asset("./assets")],
                                        destination_bucket=glue_assets_bucket,
                                        destination_key_prefix="glue_jobs"
                                        )

        # Grant Read/Write to glue role for S3
        bucket_raw_data.grant_read(glue_job_role)
        glue_assets_bucket.grant_read_write(glue_job_role)
        bucket_processed_data.grant_write(glue_job_role)




        # Create SQS queue
        queue = sqs.Queue(self, "SQSQueue",
                          visibility_timeout=Duration.seconds(300),
                          queue_name=f"ag-tech-dev-us-1-{construct_id.lower()}")
        

        # Create event notificaton for bucket to  queue
        bucket_raw_data.add_event_notification(s3.EventType.OBJECT_CREATED,
                                                     s3_notifications.SqsDestination(queue),
                                                     s3.NotificationKeyFilter(prefix="raw/")
                                                     )
        # Lambda inline ploicy to start glue job
        region = Stack.of(self).region
        account = Stack.of(self).account

         # Create Glue Job
        job = glue.CfnJob(self, "GlueJob",
                          name=f"ag-tech-dev-us-1-{construct_id.lower()}",
                          role=glue_job_role.role_arn,
                          glue_version= "4.0",
                          number_of_workers=2,
                          worker_type="G.1X",
                          default_arguments={"--job-language": "python"},
                          command=glue.CfnJob.JobCommandProperty(
                              name="glueetl",
                              script_location=f"s3://{glue_assets_bucket.bucket_name}/glue_jobs/transformation.py"
                          )
        )


        glue_job_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["glue:StartJobRun"],
            resources=[f"arn:aws:glue:{region}:{account}:job/{job.name}"]
        )

        # Iam policy
        lambda_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["s3:GetObject", "s3:PutObject"],
            resources=[f"{bucket_raw_data.bucket_arn}/*",
                       f"{bucket_processed_data.bucket_arn}/*"
                       ]
            )
        lambda_role = iam.Role(self, "LambdaRole",
                                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                role_name=f"ag-tech-dev-us-1-{construct_id.lower()}-lambda-role"
                                )
        lambda_role.add_to_policy(lambda_policy)
        lambda_role.add_to_policy(glue_job_policy)
        lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))



        # lambda_fn = alambda_.PythonFunction(self, "S3GlueRedshiftLambda",
        #                                     index="transform.py",
        #                                     entry="lambda",
        #                                     runtime=_lambda.Runtime.PYTHON_3_10,
        #                                     memory_size=1024,
        #                                     timeout=Duration.seconds(300),
        #                                     handler="lambda_handler",
        #                                     role = lambda_role, 
        #                                     environment={
        #                                         "database_name" : glue_crawler.database_name,
        #                                         "table_name" : "test_table"
        #                                         }
        #                                     )

        lambda_fn = _lambda.Function(self,"GlueHandler",
                                     runtime=_lambda.Runtime.PYTHON_3_10,
                                     handler="glue.lambda_handler",
                                     code=_lambda.Code.from_asset("functions"),
                                     role=lambda_role,
                                     timeout=Duration.seconds(300),
                                     environment={
                                         "JOB_NAME" : job.name
                                         }
                                     ) 
        
        # add sqs queue as event src for lambda
        lambda_fn.add_event_source(event_sources.SqsEventSource(queue)
                                                      )
        # Read Pemissions for the lambda
        lambda_fn.add_to_role_policy(iam.PolicyStatement(
                                                        effect=iam.Effect.ALLOW,
                                                        resources=[f"{bucket_processed_data.bucket_arn}/*"],
                                                        actions=["s3:GetObject"]
                                                        )
                                                        )
        





                
                                  

