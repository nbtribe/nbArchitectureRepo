from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    CfnOutput,
    CfnParameter,
    aws_iam as iam,
    aws_s3 as s3,
    aws_redshiftserverless,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_lambda as _lambda,
    aws_events,
    aws_events_targets,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_apigateway as apigw,
    aws_logs as logs
)
from constructs import Construct
import os.path as path

dirname = path.dirname(__file__)

class IntegrationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        REGION = self.region
        ACCOUNT = self.account

        # Create Basic execution role 
        check_if_files_exist_fn_role = iam.Role(
            self, "check_if_files_exist_fn_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")],
        )

        """Policy to give lambda permission to access S3"""
        lambda_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=["*"],
            actions=[
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
                        ],
        )
        """Add policy to role"""
        check_if_files_exist_fn_role.add_to_policy(lambda_policy)


        autoDeploy_role = iam.Role(
            self, "autoDeploy_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")],
        )     
        """Policy to give lambda permission to access S3"""
        autoDeploy_role.add_to_policy(lambda_policy)
        """Policy to give lambda permission to access Secrets Mgr"""
        autoDeploy_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=["*"],
            actions=[
                "secretsmanager:GetSecretValue",
                        ],
            
        ))

        """Policy to give lambda permission to access Redshift serverless"""
        """{PLACEHOLDER}"""


        
        check_if_files_exist_fn = _lambda.Function(self, "Check_If_Integration_Files_Exist",
                                                   
                                                #    function_name= f"""{self.stack_name}-CheckIfFilesExist""",
                                                      runtime=_lambda.Runtime.PYTHON_3_9,
                                                      role=check_if_files_exist_fn_role,
                                                      handler="check_api_files_exist.lambda_handler",
                                                      code=_lambda.Code.from_asset(f"""lambda/check_files_exist"""),
                                                      timeout=Duration.seconds(300),
                
                                                    #   environment={"CLIENT_BUCKET": client_bucket.value_as_string,
                                                    #                "SOURCE_SYSTEM": f"""{SOURCE_SYS.value_as_string}""",
                                                    #                "PREFIX": "integration_sample_files/"}
                                                                   

        )

        create_sql_scripts_files_fn = _lambda.Function(self, "CreateSqlScripts",

                                                    #    function_name= f"""{self.stack_name}-CreateSqlScripts""",
                                                       runtime=_lambda.Runtime.PYTHON_3_9,
                                                       role=check_if_files_exist_fn_role,
                                                       handler="create_sql_scripts.lambda_handler",
                                                       code=_lambda.Code.from_asset(f"""lambda/create_sql_scripts"""),
                                                       timeout=Duration.seconds(300),
                                                       environment= {"IAM_ROLE" : f"arn:aws:iam::{ACCOUNT}:role/A2_RS_A1_ROLE"}
                                                       
                                                                    # "CLIENT_BUCKET": client_bucket.value_as_string,
                                                                    # "DEPLOYMENT_BUCKET" : deployment_bucket.value_as_string,
                                                                    # "SOURCE_SYSTEM": f"""{SOURCE_SYS.value_as_string}""",
                                                                    # "PREFIX": "integration_sample_files/",
                                                                    # "IAM_ROLE" : f"arn:aws:iam::{ACCOUNT}:role/A2_RS_A1_ROLE",
                                                                    # "CUSTOMER": f"{CUSTOMER.value_as_string}"}
        )       

        """Run CREATE TABLE SCRIPTS"""
        run_sql_scripts_fn = _lambda.Function(self, "ExecSQLCreateTables",
                                            #   function_name= f"""{self.stack_name}-ExecSQLCreateTables""",
                                              runtime=_lambda.Runtime.PYTHON_3_9,
                                              role=autoDeploy_role,
                                              handler="exec_sql_create_tables.lambda_handler",
                                              code=_lambda.Code.from_asset(f"""lambda/exec_sql_create_tables"""),
                                              timeout=Duration.seconds(300),
                                            #   environment={"CLIENT_BUCKET": client_bucket.value_as_string,
                                            #                "DEPLOYMENT_BUCKET": deployment_bucket.value_as_string,
                                            #                "SOURCE_SYSTEM": f"""{SOURCE_SYS.value_as_string}""",
                                            #                "PREFIX": "integration_sample_files/",
                                            #                "IAM_ROLE": f"arn:aws:iam::{ACCOUNT}:role/A2_RS_A1_ROLE",
                                            #                "CUSTOMER": f"{CUSTOMER.value_as_string}"}
        )
                                                                         
      
        """Lambda to Create the DAG from the customer integration"""
        create_dag_fn = _lambda.Function(self, "CreateDAG",
                                        #  function_name= f"""{self.stack_name}-CreateDAG""",
                                         runtime=_lambda.Runtime.PYTHON_3_9,
                                         role=autoDeploy_role,
                                         handler="create_DAG.lambda_handler",
                                         code=_lambda.Code.from_asset(f"""lambda/create_DAG"""),
                                         timeout=Duration.seconds(300),
        )
                                                                        
        
        # # SNS Fail for Step Fn
        # fail_topic = sns.Topic(self, "FailTopic",
        #                        topic_name= f"""{CUSTOMER}_{SOURCE_SYS}-integration-Deployment-Fail"""
        #                        )

        # fail_topic.add_subscription(
        #     sns_subs.EmailSubscription("XXXXXXXXXXXXXXXXXX"),
        #     subscription_name=f"""{CUSTOMER}_{SOURCE_SYS}-integration-Deployment-Fail"""
        #                        )    

        # # SNS Success for Step Fn
        # success_topic = sns.Topic(self, "SuccessTopic",
        #                           topic_name= f"""{CUSTOMER}_{SOURCE_SYS}-integration-Deployment-Success"""
        #                           )
        # success_topic.add_subscription(
        #     sns_subs.EmailSubscription("XXXXXXXXXXXXXXXXXX"),
        #     subscription_name=f"""{CUSTOMER}_{SOURCE_SYS}-integration-Deployment-Success"""
            
        #                           )

        """Step Fn Role"""
        # step_fn_role = iam.Role(

        # Create step function
        # start_state = sfn.Pass(self, "Start State",
        #                         parameters={
        #                             "message": "Integration Deployment Started"
        #                             }).next(check_if_files_exist_task).next()

        

        check_if_files_exist_task = tasks.LambdaInvoke(self, "Check if files exist",
                                                        lambda_function=check_if_files_exist_fn,
                                                        result_path="$.filePresentStatus",
                                                        )
        are_sample_files_present_task = sfn.Choice(self, "Are Sample Files Present?"
                                                        )

        create_sql_scripts_files_task = tasks.LambdaInvoke(self, "Create SQL Scripts",
                                                            lambda_function=create_sql_scripts_files_fn,
                                                            result_path="$.filePresentStatus"
                                                        )
        """WAIT STATE - NOT USED in STEp Fn"""
        wait_state = sfn.Wait(self, "Wait for Create SQL Scripts",
                                                     time = sfn.WaitTime.duration(Duration.seconds(10))
                                                        )
        run_sql_scripts_task = tasks.LambdaInvoke(self, "Run SQL Scripts",
                                                  lambda_function=run_sql_scripts_fn,
                                                  result_path="$.filePresentStatus"
                                                  )
        create_dag_task = tasks.LambdaInvoke(self, "Create DAG",
                                             lambda_function=create_dag_fn,
                                             result_path="$.filePresentStatus")

        """Step Fn Def"""
        machine_definition = sfn.Pass(self,"PassState", 
                            ).next(check_if_files_exist_task
                                   ).next(are_sample_files_present_task.when(sfn.Condition.boolean_equals("$.filePresentStatus.Payload.filePresentStatus",
                                                    True),
                                                    create_sql_scripts_files_task
                                                     ).otherwise(sfn.Fail(self,
                                                                "Sample Files Not Present",
                                                                cause="Sample Files Not Present",
                                                                error="Sample Files Not Present"
                                                                )
                                                                ).afterwards()
                                                                # .next(wait_state)
                                                                .next(run_sql_scripts_task)
                                                                .next(create_dag_task)
                                          )
                                                        
        state_machine_log_group = logs.LogGroup(self, f"""State_Machine_LogGroup""",
                                                # log_group_name = f"""{self.stack_name}-_State_Machine_LogGroup""",
                                                removal_policy = RemovalPolicy.DESTROY,
                                                # retention = logs.RetentionDays
                                                )
        

        state_machine = sfn.StateMachine(self, """State_Machine""", 
                definition = machine_definition, 
                # state_machine_name = f"""{self.stack_name}-Auto_integration_Deploy_State_Machine""",
                timeout=Duration.minutes(10),
                tracing_enabled=True,
                logs=sfn.LogOptions(level=sfn.LogLevel.ALL,
                                    
                                    
                                    destination =state_machine_log_group, 
                                    include_execution_data = True,
                                        ),
                state_machine_type = sfn.StateMachineType.EXPRESS)
        
        """API Gateway"""
        api = apigw.StepFunctionsRestApi(self, 
                         f"-{self.stack_name}-RestApi",
                    # rest_api_name = f"""{self.stack_name}-RestApi""",
                    deploy_options= apigw.StageOptions(stage_name = "dev"),
                    state_machine = state_machine)
        


        
