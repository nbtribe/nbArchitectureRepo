from constructs import Construct
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct

class ServerlessWebAppResumeChallengeStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        webapp_bucket = s3.Bucket(
            self,
            "WebApp-Bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=True,
            versioned=True,
            
        )
        
        webapp_bucket.add_cors_rule(
            allowed_methods=[s3.HttpMethods.GET],
            allowed_origins=["*"],
            allowed_headers=["*"],
            exposed_headers=["Access-Control-Allow-Origin"]
        )

        oai = cloudfront.OriginAccessIdentity(
            self,
            "OAI",
            comment="My OAI for the S3 Website"
        )

        webapp_bucket.grant_read(oai)


        cdist = cloudfront.Distribution(self, "myCloudFrontDistribution",
            default_root_object='web/index.html',
            default_behavior=cloudfront.BehaviorOptions(
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                origin=origins.S3Origin(webapp_bucket, origin_access_identity=oai),
                origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN, 
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS,
                
                
                )
        )

        # Dynamo Setup
        dynamo_table = dynamodb.Table(
            self,
            "Dynamo-Table",
            removal_policy=RemovalPolicy.DESTROY,
            table_name="visitorCounter",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),

        )

        # IAM execution role for Lambda 
        exec_role = iam.Role(
            self,
    
            "ServerlessWebAppLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")],
        )

        # Not ideal but for this example I add full access to Dynamo for the Lambda Execution Role
        exec_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"))

        # Lambda Setup
        """Lambda Fn will read dynamo to get number of visitors"""
        lambda_fn = _lambda.Function(
            self,
            "ServerlessWebAppLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="lambda_function.lambda_handler",
            role=exec_role,
            
        )
        
        lambda_fn.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
            cors = _lambda.FunctionUrlCorsOptions(
                allowed_origins=["*"],
            )

        )


        