from aws_cdk import (
    # Duration,
    Stack,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as alambda_,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    Duration,
    RemovalPolicy
)
from constructs import Construct
import os.path as path

class MsTeamsEtlAlertBotStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
            super().__init__(scope, construct_id, **kwargs)

            # The code that defines your stack goes here
            #Existing Role
            lambda_role = iam.Role.from_role_arn(self, "lambda_role",
                                                "arn:aws:iam::<AWS_ACCOUNT>:role/EAA_Lambda_basic_execution")
            
            
            mta_daily_ms_teams_alert_lambda_fn = alambda_.PythonFunction(self, "MTA_Daily_MsTeams_Function",
                index="mta_alert_daily.py",
                entry="src/mta_daily_lambda_fn",
                memory_size=1024,
                timeout=Duration.seconds(300),                
                description="MTA Daily MS Teams Alert ETL",                                        
                runtime=lambda_.Runtime.PYTHON_3_7,
                handler="lambda_handler",
                role = lambda_role,
                # Add psycopg2 v4 layer manually
                )

            late_running_daily_ms_teams_alert_lambda_fn = alambda_.PythonFunction(self, "Late_Running Daily_MsTeams_Function",
                index="late_running_alert_daily.py",
                entry="src/late_running_daily_lambda_fn",
                memory_size=1024,
                timeout=Duration.seconds(300),                
                description="Late Running - Daily MS Teams Alert ETL",                                        
                runtime=lambda_.Runtime.PYTHON_3_7,
                handler="lambda_handler",
                role = lambda_role,
                # Add psycopg2 v4 layer manually
                )
            
            daily_ms_teams_alert_lambda_fn = alambda_.PythonFunction(self, "Daily_MsTeams_Function",
                index="alert_daily.py",
                entry="src/daily_lambda_fn",
                memory_size=1024,
                timeout=Duration.seconds(300),                
                description="Daily MS Teams Alert ETL",                                        
                runtime=lambda_.Runtime.PYTHON_3_7,
                handler="lambda_handler",
                role = lambda_role,
                # Add psycopg2 v4 layer manually
                )
            
            weekly_ms_teams_alert_lambda_fn = alambda_.PythonFunction(self, "Weekly_MsTeams_Function",
                index="alert_weekly.py",
                entry="src/weekly_lambda_fn",
                memory_size=1024,
                timeout=Duration.seconds(300),                
                description="Weekly MS Teams Alert ETL",                                        
                runtime=lambda_.Runtime.PYTHON_3_7,
                handler="lambda_handler",
                role = lambda_role,
                # Add psycopg2 v4 layer manually
                )
            
            monthly_ms_teams_alert_lambda_fn = alambda_.PythonFunction(self, "Monthly_MsTeams_Function",
                index="alert_monthly.py",
                entry="src/monthly_lambda_fn",
                memory_size=1024,
                timeout=Duration.seconds(300),                
                description="Monthly MS Teams Alert ETL",                                        
                runtime=lambda_.Runtime.PYTHON_3_7,
                handler="lambda_handler",
                role = lambda_role,
                # Add psycopg2 v4 layer manually
                )
            
            
            # Time is UTC so hour = 12 for 8AM run
            # EventBridge Rule
            
            mta_daily_rule = events.Rule(self, "MTA Daily MSTeamsETLAlertRule",
                            schedule = events.Schedule.cron(minute="0",hour="12",day="*",month="*",year="*"),
                            targets=[targets.LambdaFunction(mta_daily_ms_teams_alert_lambda_fn)],
                            enabled=True,
                                                        )
            
            late_running_daily_rule = events.Rule(self, "Late Running Daily MSTeamsETLAlertRule",
                            schedule = events.Schedule.cron(minute="0",hour="16",day="*",month="*",year="*"),
                            targets=[targets.LambdaFunction(late_running_daily_ms_teams_alert_lambda_fn)],
                            enabled=True,
                                                        )
            daily_rule = events.Rule(self, "Daily MSTeamsETLAlertRule",
                            schedule = events.Schedule.cron(minute="0",hour="12",day="*",month="*",year="*"),
                            targets=[targets.LambdaFunction(daily_ms_teams_alert_lambda_fn)],
                            enabled=True,
                                                        )
            
            weekly_rule = events.Rule(self, "Weekly MSTeamsETLAlertRule",
                            schedule = events.Schedule.cron(week_day="Monday",minute="0",hour="12",year="*"),
                            targets=[targets.LambdaFunction(weekly_ms_teams_alert_lambda_fn)],
                            enabled=True,
                            )
            
            monthly_rule = events.Rule(self, "Monthly MSTeamsETLAlertRule",
                            schedule = events.Schedule.cron(day="15",minute="0",hour="12",year="*"),
                            targets=[targets.LambdaFunction(monthly_ms_teams_alert_lambda_fn)],
                            enabled=True,
                            )
