import os
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb_,
    aws_lambda as lambda_,
    aws_apigateway as apigw_,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_scheduler as scheduler,


    
    Duration,
)
from constructs import Construct

TABLE_NAME = "lawncare-contacts-table"

class ServerlessLawncareAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        
        
        # Create the send Lambda
        send_lambda = lambda_.Function(self, "send_lambda_function",
                                       runtime=lambda_.Runtime.PYTHON_3_10,
                                       handler="send.handler",
                                       code=lambda_.Code.from_asset("lambda"),
                                       role=iam.Role(self, "send_lambda_role",
                                                     assumed_by=iam.ServicePrincipal(
                                                         "lambda.amazonaws.com"),
                                                     managed_policies=[
                                                         iam.ManagedPolicy.from_aws_managed_policy_name(
                                                             "service-role/AWSLambdaBasicExecutionRole"
                                                         )
                                                     ]
                                                     )
                                       environment={
                                           "TOPIC_ARN": SNS_TOPIC_ARN,
                                       }
                                       )
        
        # Lambda Role
        send_lambda.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["sns:Publish"],
            resources=[SNS_TOPIC_ARN]
        )
        )
            
        
        # create a role and a policy to allow running associations
        schedulerRole = iam.Role(self, 'lawn-care-scheduler-role',
            assumed_by=iam.ServicePrincipal('scheduler.amazonaws.com'))
        
        # add policy to role
        schedulerRole.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["lambda:InvokeFunction"]
            resources=[lambda_function.function_arn]

        
        # schedule to run every Sunday at 2:00am
        schedule = scheduler.CfnSchedule(self, 'run-command',
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            schedule_expression='cron(0 2 ? * SUN *)',
            target=scheduler.CfnSchedule.TargetProperty(
                    arn='arn:aws:scheduler:::aws-sdk:ssm:startAssociationsOnce',
                    role_arn=schedulerRole.role_arn,
                    input=json.dumps({"AssociationIds": [cfnAssociation.attr_association_id]})
            )
        )




        # # VPC
        # vpc = ec2.Vpc(
        #     self,
        #     "Ingress",
        #     ip_addresses="10.1.0.0/16",
        #     subnet_configuration=[
        #         ec2.SubnetConfiguration(
        #             name="Private-Subnet", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
        #             cidr_mask=24
        #         )
        #     ],
        # )
        
        # # Create VPC endpoint
        # dynamo_db_endpoint = ec2.GatewayVpcEndpoint(
        #     self,
        #     "DynamoDBVpce",
        #     service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
        #     vpc=vpc,
        # )

        # # This allows to customize the endpoint policy
        # dynamo_db_endpoint.add_to_policy(
        #     iam.PolicyStatement(  # Restrict to listing and describing tables
        #         principals=[iam.AnyPrincipal()],
        #         actions=[                "dynamodb:DescribeStream",
        #         "dynamodb:DescribeTable",
        #         "dynamodb:Get*",
        #         "dynamodb:Query",
        #         "dynamodb:Scan",
        #         "dynamodb:CreateTable",
        #         "dynamodb:Delete*",
        #         "dynamodb:Update*",
        #         "dynamodb:PutItem"],
        #         resources=["*"],
        #     )
        # )

        # # Create DynamoDb Table
        # demo_table = dynamodb_.Table(
        #     self,
        #     TABLE_NAME,
        #     partition_key=dynamodb_.Attribute(
        #         name="id", type=dynamodb_.AttributeType.STRING
        #     ),
        # )

        # # Create the Lambda function to receive the request
        # api_hanlder = lambda_.Function(
        #     self,
        #     "ApiHandler",
        #     function_name="apigw_handler",
        #     runtime=lambda_.Runtime.PYTHON_3_9,
        #     code=lambda_.Code.from_asset("lambda"),
        #     handler="index.handler",
        #     vpc=vpc,
        #     vpc_subnets=ec2.SubnetSelection(
        #         subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
        #     ),
        #     memory_size=1024,
        #     timeout=Duration.minutes(1),
        # )

        # # grant permission to lambda to write to contacts table
        # demo_table.grant_write_data(api_hanlder)
        # api_hanlder.add_environment("TABLE_NAME", demo_table.table_name)

        # # Create API Gateway
        # apigw_.LambdaRestApi(
        #     self,
        #     "Endpoint",
        #     handler=api_hanlder,
        # )




    
        
