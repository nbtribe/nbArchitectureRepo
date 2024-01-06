
import os
from aws_cdk import (
    Duration,
    Stack,
    RemovalPolicy,
    aws_apigateway as apigw,
    aws_sns as sns,
    aws_lambda as lambda_,
    aws_apigateway as apigw_,
    aws_iam as iam,
    aws_s3 as s3,
    aws_kinesisfirehose as firehose,
    
)
from constructs import Construct

class DataAnalyticsCaptureClickstreamSolutionStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        # IAM plolicy
        s3_put_firehose_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["firehose:PutRecord"],
            resources=["*"],
            sid="VisualEditor0"
        )
        # IAM Role
        s3_put_firehose_role = iam.Role(self, "s3_put_firehose_role",
                                        assumed_by= iam.ServicePrincipal("firehose.amazonaws.com"),
                                     )
        
        # Attach the IAM policy to the IAM role
        s3_put_firehose_role.add_to_policy(s3_put_firehose_policy)

        # Create an S3 bucket to store clickstream data
        s3_bucket = s3.Bucket(self, f"nb-arch-clickstream-{construct_id}",
                              removal_policy=RemovalPolicy.DESTROY,
                            #   auto_delete_objects=True,
                              versioned=True,
                              encryption=s3.BucketEncryption.S3_MANAGED,
                              block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        bucket_policy = iam.PolicyStatement( 
            effect=iam.Effect.ALLOW,
            principals=[iam.ArnPrincipal(s3_put_firehose_role.role_arn)],
            actions=["s3:AbortMultipartUpload",
                     "s3:GetBucketLocation",
                     "s3:GetObject",
                     "s3:ListBucket",
                     "s3:ListBucketMultipartUploads",
                     "s3:PutObject",
                     "s3:PutObjectAcl"],
            resources=[s3_bucket.bucket_arn,
                                s3_bucket.bucket_arn + "/*"],
            sid="StmtID"
            )
        
        # s3_bucket.add_to_resource_policy(bucket_policy)
    


        lambda_function = lambda_.Function(self, "ClickstreamLambda",
                                            runtime=lambda_.Runtime.PYTHON_3_9,
                                            handler="process.lambda_handler",
                                            code=lambda_.Code.from_asset("lambda/process_fn"),
                                            environment={"BUCKET_NAME": s3_bucket.bucket_name},
                                            timeout=Duration.seconds(10)
                                            )
        
        
        kinesis_ds = firehose.CfnDeliveryStream(self, "DeliveryStream",
                                                delivery_stream_name="nb-arch-clickstream-DS",
                                                delivery_stream_type="DirectPut",
                                            
                                                 s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                                                     bucket_arn= s3_bucket.bucket_arn,
                                                     role_arn=s3_put_firehose_role.role_arn,
                                                     cloud_watch_logging_options=firehose.CfnDeliveryStream.CloudWatchLoggingOptionsProperty(
                                                         enabled=True,
                                                         log_group_name="DeliveryStream",
                                                         log_stream_name="Clickstream")
                                                     ),
                                                extended_s3_destination_configuration = 
                                                    firehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
                                                        buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
                                                            interval_in_seconds=60,
                                                            size_in_m_bs=1
                                                        ),
                                                    processing_configuration=
                                                        firehose.CfnDeliveryStream.ProcessingConfigurationProperty(
                                                            enabled=True,
                                                            processors=[firehose.CfnDeliveryStream.ProcessorProperty(
                                                                type="Lambda",
                                                                parameters=[firehose.CfnDeliveryStream.ProcessorParameterProperty(
                                                                    parameter_name="LambdaArn",
                                                                    parameter_value=lambda_function.function_arn
                                                                    )]   )]                                  
        )
        )
                                                    )

                                                    
                                                


        # kinesis_ds.ProcessingConfigurationProperty(
        #                             enabled=True,
        #                             processors=[firehose.CfnDeliveryStream.ProcessorProperty(
        #                                 type="Lambda",
        #                                 parameters=[firehose.CfnDeliveryStream.ProcessorParameterProperty(
        #                                     parameter_name="LambdaArn",
        #                                     parameter_value=lambda_function.function_arn

        #                                 )]
        #                             )]
        # )

        api_gateway = apigw.RestApi(self, "ClickstreamApi",
                                    rest_api_name="ClickstreamApi",
                                    description="Clickstream API",
                                    
                                    )
        api_gateway.root.add_resource("poc").add_method("POST",
                                                        apigw.AwsIntegration(service="firehose",
                                                         action="PutRecord",
                                                         integration_http_method="POST",
                                                         region="us-east-1",
                                                         options=apigw.IntegrationOptions(
                                                            #  NEED TO LOOK AT THIS ROLE ON WHAT NEEDS TO ASSUME WHAT?!?!?!
                                                             credentials_role=s3_put_firehose_role,
                                                             passthrough_behavior= apigw.PassthroughBehavior.WHEN_NO_TEMPLATES,
                                                             request_templates={"application/json": "{\"DeliveryStreamName\":\"nb-arch-clickstream-DS\", \"Record\":{\"Data\":\"$input.body\"}}"},
                                                             integration_responses=[apigw.IntegrationResponse(
                                                                 status_code="200",
                                                                 response_templates={"application/json": "OK"}
                                                                 )],


                                    )
                                    )
        )
                                                                

        # api_gateway.root.add_method("POST",
        #                             apigw.AwsIntegration(service="firehose",
        #                                                  action="PutRecord",
        #                                                  integration_http_method="POST",
        #                                                  region="us-east-1",
        #                                                  options=apigw.IntegrationOptions(
        #                                                      credentials_role=s3_put_firehose_role,
        #                                                      passthrough_behavior= apigw.PassthroughBehavior.WHEN_NO_TEMPLATES,
        #                                                      request_templates={"application/json": "{\"DeliveryStreamName\":\"nb-arch-clickstream-DS\", \"Record\":{\"Data\":\"$input.body\"}}"},
        #                                                      integration_responses=[apigw.IntegrationResponse(
        #                                                          status_code="200",
        #                                                          response_templates={"application/json": "OK"}
        #                                                          )],


        #                             )
        #                             )
        # )
                                    

        # api_gateway.AwsIntegration(service="firehose",
        #                                    action="PutRecord",
        #                                    integration_http_method="POST",
        #                                    region="us-east-1",
        #                                 #    path="poc",
        #                                    options=apigw.IntegrationOptions(
        #                                        credentials_role=s3_put_firehose_role,   
        #                                        request_templates={"application/json": "{\"DeliveryStreamName\":\"nb-arch-clickstream-DS\", \"Record\":{\"Data\":\"$input.body\"}}"},
        #                                        integration_responses=[apigw.IntegrationResponse(
        #                                            status_code="200",
        #                                            response_templates={"application/json": "OK"}
        #                                            )],
        #                                        passthrough_behavior=apigw.PassthroughBehavior.NEVER,
        #                                        request_parameters={"integration.request.header.Content-Type": "'application/json'"},
        #                                        content_handling=apigw.ContentHandling.CONVERT_TO_TEXT,
        #                                        timeout=Duration.seconds(10)
        #                                        )      
        #                                    )
        # api_gateway.add
                                          
