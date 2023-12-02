from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_pinpoint as pinpoint,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_events as events,
    aws_scheduler as scheduler,
    # aws_scheduler_alpha as _aschedule,
    
    

)
from constructs import Construct

class ServerlessLawncareAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # PINPOINT
        
        pinpoint_app = pinpoint.CfnApp(self, "PinpointApp", 
                                           name="KTI SMS"
        )
        #  Add email channel to pinpoint app
        cfn_email_channel = pinpoint.CfnEmailChannel(self, "EmailChannel",
            application_id=pinpoint_app.ref,
            from_address="no-reply@trybegenapi.link",
            identity="arn:aws:ses:us-east-1:625543658497:identity/trybegenapi.link",
            # the properties below are optional
            enabled=True,
            # role_arn="roleArn"
        )

        #  Add SNS channel to pinpoint app
        cfn_sms_channel = pinpoint.CfnSMSChannel(self, "SMSChannel",
            application_id=pinpoint_app.ref,
            enabled=True,
            sender_id="TrybeGenAPI",
            short_code="shortCode"
        )


        target_lambda = _lambda.Function(self, "target_lambda",
                                         runtime=_lambda.Runtime.PYTHON_3_9,
                                         code=_lambda.Code.from_asset("lambda"),
                                         handler="lambda.handler",
                                         )


        jan_schedule = scheduler.CfnSchedule(self, "jan_schedule",
                                             flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                                                 mode="OFF",),
                                             schedule_expression="cron(00 10 25 1 ? *)",

                                            
        )

#         target = targets.LambdaInvoke(fn,
#             input=ScheduleTargetInput.from_object({
#             "payload": "useful"
#     })
# )
#         # EVENTBRIDGE Scheduler
#         january_schedule = _aschedule.Sche(self,"Jan_Schedule",
#                                       schedule =_aschedule.ScheduleExpression.cron(minute="0", hour="10",day="25", month="1", year="*" )
#         )

    
        
