from aws_cdk import (
    Duration,
    BootstraplessSynthesizer,
    Environment,
    Stack,
    Stage,
    StackProps,
    RemovalPolicy,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    CfnParameter,
    CfnOutput,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_s3_notifications as s3n
)
from constructs import Construct
from auto_integration_deployments.integration_stack import IntegrationStack
from auto_integration_deployments.integration_code_pipeline import IntegrationCodePipeline
import os.path as path


dirname = path.dirname(__file__)

class AutoIntegrationDeploymentsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        REGION = self.region
        ACCOUNT = self.account


        source_system = CfnParameter(self, "SourceSystem", type="String",
                                     description="Source System",
        )
        source_system_str = source_system.value_as_string

        bucketTemplates = s3.Bucket(self, "bucketTemplates",
                                    bucket_name= f"{ACCOUNT}-{REGION}-bucket-templates",
                                    
                                    removal_policy=RemovalPolicy.RETAIN,
                                    versioned=True,
                                    public_read_access=False,
                                    block_public_access=s3.BlockPublicAccess.BLOCK_ALL)
        
        lambda_role = iam.Role(self, f"LambdaS3DeployCfnRole",
                                   role_name=f"CfnIntegrationDeploy-lambda-role",
                                   assumed_by=iam.CompositePrincipal( 
                                       iam.ServicePrincipal("lambda.amazonaws.com"),
                                       iam.ServicePrincipal("cloudformation.amazonaws.com")),
                                   managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")])

        # grant role accesss to s3 
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=["*"],
            actions=[
                "states:*",
                "logs:*",
                "lambda:*",
                "apigateway:*",
                "ssm:GetParameters",
                "iam:*",
                "iam:PassRole",
                "iam:CreateRole",
                "iam:DeleteRole",
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
            ],
        )
        )

        # grant role accesss to cloudformation
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=["*"],
            actions=[
                "cloudformation:CreateStack",
                "cloudformation:DeleteStack",
                "cloudformation:DescribeStacks",
                "cloudformation:UpdateStack",
                "cloudformation:GetTemplate",
                "cloudformation:ValidateTemplate",
            ],
            )
        )

        

        lambda_deploy_cfn_template = lambda_.Function(self, "LambdaDeployCfnTemplate",
                                                      role = lambda_role,
                                                      timeout=Duration.seconds(300),
                                                       runtime=lambda_.Runtime.PYTHON_3_9,
                                                       handler="deploy_cfn_template.lambda_handler",
                                                       code=lambda_.Code.from_asset(path.join(dirname, "lambda/deploy_cfn_template")),
                                                       environment={"bucket_name": bucketTemplates.bucket_name,
                                                                    "source_system": source_system_str,
                                                                    "roleArn": lambda_role.role_arn},
                                                       )
        ########## Making the Lambda to deploy CFN template when uploaded to bucket- S# event notification
                                                      

        bucketTemplates.add_event_notification(s3.EventType.OBJECT_CREATED,
                                               s3n.LambdaDestination(lambda_deploy_cfn_template),
                                               s3.NotificationKeyFilter(prefix="integrations/"),
                                               s3.NotificationKeyFilter(suffix=".template.json")
                                               )
        
        # Create a stage to synthesize the stack
        stage = Stage(self, f"DemoStage",
                      stage_name="DemoStage",

                      
        )

        

        # Integration stack Stack cfn synthesize
        #                                      )
        integration_stack = IntegrationStack(stage, "IntegrationStack", 
                                             
                                             )

        
        # synthesizer=BootstraplessSynthesizer()
                                             

        # Force Synth
        assembly = stage.synth()
        print(assembly.stacks)


        templateFullPath = assembly.stacks[0].template_full_path
        template_directory = path.dirname(templateFullPath)
        print(f"TEMPLAtFULLPATHNAME = {templateFullPath}")
        templateFileName = path.basename(templateFullPath)
        print(f"TEMPLATEFILENAME = {templateFileName}")
        print(f"TEMPLATEDIR = {template_directory}")

        deployStack = s3_deployment.BucketDeployment(self, "DeployStack",
                                                    #  sources=[s3_deployment.Source.asset(f"{templateFullPath}.zip")],
                                                    #  sources=[s3_deployment.Source.asset(
                                                    #      path.join(dirname, templateFullPath))],
                                                         sources = [s3_deployment.Source.asset(template_directory,exclude=[f"{templateFileName.split('.')[0]}.assets.json"])],
                                                         destination_bucket=bucketTemplates,
                                                        destination_key_prefix=f"integrations/{source_system.value_as_string}",        

        )

        CfnOutput(self, "SourceSystemName", value=source_system.value_as_string)
