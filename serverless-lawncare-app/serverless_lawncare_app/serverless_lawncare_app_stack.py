import os
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb_,
    aws_lambda as lambda_,
    aws_apigateway as apigw_,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_events as events,
    aws_scheduler as scheduler,
    aws_apigateway as apigw,
    aws_sns as sns,
    CfnOutput,
    Duration,
    aws_events_targets as targets
)
from constructs import Construct

# TABLE_NAME = "lawncare-contacts-table"

class ServerlessLawncareAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Will add frontend with APIGW later on
        # # REST API
        # reminderAPI= apigw.RestApi(self, f"{construct_id}-reminderAPI_Reminder Lawncare",
        #                            endpoint_types=[apigw.EndpointType.REGIONAL],
        #                            description="This service allows users to create and manage reminders.",
        #                            deploy=False,
        #                            retain_deployments=False
                                   
        #                            )
        # deployment = apigw.Deployment(self, "Deployment",
        #                               api=reminderAPI,
        #                               retain_deployments=False
        #                               )
        # stage=apigw.Stage(self, "dev",
        #                   deployment=deployment,

        
                                      
        # Create the event bus
        eventBus = events.EventBus(self, f"{construct_id}-event-bus",
                                   event_bus_name=f"{construct_id}-lawncare-event-bus"
                                   )
        


        iam.Policy(self, f'{construct_id}-scheduler-policy',
                   policy_name='ScheduleToPutEvents',
                   statements=[
                       iam.PolicyStatement(
                           effect=iam.Effect.ALLOW,
                           actions=["events:PutEvents"],
                           resources=[eventBus.event_bus_arn]
                       )
                   ]
        )


        # SNS Topic
        sns_topic = sns.Topic(self, "TrybeLawncareCustomerSMSTopic"
                              )
       

        # Lamda Role
        lambda_role = iam.Role(self, "lambda_role",
                               assumed_by=iam.ServicePrincipal(
                                   "lambda.amazonaws.com"),
                               managed_policies=[
                                   iam.ManagedPolicy.from_aws_managed_policy_name(
                                       "service-role/AWSLambdaBasicExecutionRole"
                                   )
                               ]
                               )
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["sns:Publish"],
            resources=[sns_topic.topic_arn]
        )
        )
        # Create the send Lambda
        send_lambda = lambda_.Function(self, f"{construct_id}-send_lambda_function",
                                       runtime=lambda_.Runtime.PYTHON_3_10,
                                       handler="send_alert.lambda_handler",
                                       code=lambda_.Code.from_asset("lambda/send_fn"),
                                       role=lambda_role,
                                       timeout=Duration.minutes(3),
                                       environment={"SNS_TOPIC_ARN": sns_topic.topic_arn}
        )



        # need to create a service-linked role and policy for 
        # the scheduler to be able to put events onto our bus
        schedulerRole = iam.Role(self, f'{construct_id}-lawn-care-scheduler-role',
                                 assumed_by= iam.ServicePrincipal("scheduler.amazonaws.com")
        )
        # Scheduler role to invoke lambda
        schedulerRole.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["lambda:InvokeFunction"],
            resources=[f"{send_lambda.function_arn}:*",
                       send_lambda.function_arn]
        )
        )

        # schedule to run every year
        # March
        schedule = scheduler.CfnSchedule(self, 'March Schedule',
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            schedule_expression_timezone= "America/New_York",
            schedule_expression='cron(0 10 01 03 ? *)',
            target=scheduler.CfnSchedule.TargetProperty(
                arn = send_lambda.function_arn,
                role_arn = schedulerRole.role_arn,
                input= '{"message": "**Order early spring fert w/ Pre-Emergent weed Control for lawn and beds and apply -> https://www.amazon.com/s?k=spring+fertilizer"}'

        )
        )
        # April
        schedule = scheduler.CfnSchedule(self, 'April Schedule',
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            schedule_expression_timezone= "America/New_York",
            schedule_expression='cron(0 10 10 04 ? *)',
            target=scheduler.CfnSchedule.TargetProperty(
                arn = send_lambda.function_arn,
                role_arn = schedulerRole.role_arn,
                input= '{"message": "**Order Post & Pre-Emergent weed control and apply -> https://www.amazon.com/s?k=post%2Fpre+emergent+weed+control+for+lawns"}'

        )
        )
        # June/July
        schedule = scheduler.CfnSchedule(self, 'July Schedule',
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            schedule_expression_timezone= "America/New_York",
            schedule_expression='cron(0 10 27 06 ? *)',
            target=scheduler.CfnSchedule.TargetProperty(
                arn = send_lambda.function_arn,
                role_arn = schedulerRole.role_arn,
                input= '{"message": "**Order Summer barricade weed control and apply -> https://www.amazon.com/s?k=weed+barricade"}'

        )
        )
        # August
        schedule = scheduler.CfnSchedule(self, 'August Schedule',
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            schedule_expression_timezone= "America/New_York",
            schedule_expression='cron(0 10 06 08 ? *)',
            target=scheduler.CfnSchedule.TargetProperty(
                arn = send_lambda.function_arn,
                role_arn = schedulerRole.role_arn,
                input= '{"message": "**Order Liquid fert w/ weed control and apply -> https://www.amazon.com/s?k=liquid+fertilizer+and+weed+control"}'

        )
        )
        # September
        schedule = scheduler.CfnSchedule(self, 'September Schedule',
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            schedule_expression_timezone= "America/New_York",
            schedule_expression='cron(0 10 01 09 ? *)',
            target=scheduler.CfnSchedule.TargetProperty(
                arn = send_lambda.function_arn,
                role_arn = schedulerRole.role_arn,
                input= '{"message": "**Order Grass seed, Fert and schedule aeration -> https://www.amazon.com/s?k=fall+fertilizer"}'

        )
        )

        # October
        schedule = scheduler.CfnSchedule(self, 'October Schedule',
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            schedule_expression_timezone= "America/New_York",
            schedule_expression='cron(0 10 27 10 ? *)',
            target=scheduler.CfnSchedule.TargetProperty(
                arn = send_lambda.function_arn,
                role_arn = schedulerRole.role_arn,
                input= '{"message": "**Order Fall Fertilizer -> https://www.amazon.com/s?k=fall+fertilizer"}'

        )
        )
        
        # November
        schedule = scheduler.CfnSchedule(self, 'November Schedule',api
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            schedule_expression_timezone= "America/New_York",
            schedule_expression='cron(0 10 01 12 ? *)',
            target=scheduler.CfnSchedule.TargetProperty(
                arn = send_lambda.function_arn,
                role_arn = schedulerRole.role_arn,
                input= '{"message": "**Order lyme and apply anytime in Nov or Dec -> https://www.amazon.com/s?k=lyme+for+lawn"}'

        )
        )
        # December
        schedule = scheduler.CfnSchedule(self, 'December Schedule',
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            schedule_expression_timezone= "America/New_York",
            schedule_expression='cron(0 10 01 12 ? *)',
            target=scheduler.CfnSchedule.TargetProperty(
                arn = send_lambda.function_arn,
                role_arn = schedulerRole.role_arn,
                input= '{"message": "**Order winterizer fert with weed control and apply -> https://www.amazon.com/s?k=winterizer+fertilizer+with+weed+control"}'

        )
        )



        CfnOutput(self, "SNS_TOPIC_ARN1", description="SNS topic ARN", value=sns_topic.topic_arn)
                                 
        # # Lambda Role
        # send_lambda.add_to_role_policy(iam.PolicyStatement(
        #     effect=iam.Effect.ALLOW,
        #     actions=["sns:Publish"],
        #     resources=["*"]
        #     # ^^^^^ Have to filter this to the specific SNS that was made here 
        # )
        # )


        # # link up apigw and lambda
        # integration = apigw_.LambdaIntegration(send_lambda,
        #                                        proxy=True,)
      ##################################################################################################  



#         # # VPC
#         # vpc = ec2.Vpc(
#         #     self,
#         #     "Ingress",
#         #     ip_addresses="10.1.0.0/16",
#         #     subnet_configuration=[
#         #         ec2.SubnetConfiguration(
#         #             name="Private-Subnet", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
#         #             cidr_mask=24
#         #         )
#         #     ],
#         # )
        
#         # # Create VPC endpoint
#         # dynamo_db_endpoint = ec2.GatewayVpcEndpoint(
#         #     self,
#         #     "DynamoDBVpce",
#         #     service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
#         #     vpc=vpc,
#         # )

#         # # This allows to customize the endpoint policy
#         # dynamo_db_endpoint.add_to_policy(
#         #     iam.PolicyStatement(  # Restrict to listing and describing tables
#         #         principals=[iam.AnyPrincipal()],
#         #         actions=[                "dynamodb:DescribeStream",
#         #         "dynamodb:DescribeTable",
#         #         "dynamodb:Get*",
#         #         "dynamodb:Query",
#         #         "dynamodb:Scan",
#         #         "dynamodb:CreateTable",
#         #         "dynamodb:Delete*",
#         #         "dynamodb:Update*",
#         #         "dynamodb:PutItem"],
#         #         resources=["*"],
#         #     )
#         # )

#         # # Create DynamoDb Table
#         # demo_table = dynamodb_.Table(
#         #     self,
#         #     TABLE_NAME,
#         #     partition_key=dynamodb_.Attribute(
#         #         name="id", type=dynamodb_.AttributeType.STRING
#         #     ),
#         # )

#         # # Create the Lambda function to receive the request
#         # api_hanlder = lambda_.Function(
#         #     self,
#         #     "ApiHandler",
#         #     function_name="apigw_handler",
#         #     runtime=lambda_.Runtime.PYTHON_3_9,
#         #     code=lambda_.Code.from_asset("lambda"),
#         #     handler="index.handler",
#         #     vpc=vpc,
#         #     vpc_subnets=ec2.SubnetSelection(
#         #         subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
#         #     ),
#         #     memory_size=1024,
#         #     timeout=Duration.minutes(1),
#         # )

#         # # grant permission to lambda to write to contacts table
#         # demo_table.grant_write_data(api_hanlder)
#         # api_hanlder.add_environment("TABLE_NAME", demo_table.table_name)

#         # # Create API Gateway
#         # apigw_.LambdaRestApi(
#         #     self,
#         #     "Endpoint",
#         #     handler=api_hanlder,
#         # )




    
        
