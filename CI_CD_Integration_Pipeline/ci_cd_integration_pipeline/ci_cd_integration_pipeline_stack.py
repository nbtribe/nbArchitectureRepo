from aws_cdk import (
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
    aws_codedeploy as codedeploy,
    aws_codepipeline as pipeline,
    aws_codepipeline_actions as pipelineactions,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    CfnOutput,
    Stack,
    Environment,
    pipelines,
    CfnParameter,
    SecretValue,
    RemovalPolicy,
    Duration,
    aws_logs as logs)
from constructs import Construct
import os

class CiCdIntegrationPipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        
        git_input =pipelines.CodePipelineSource.connection(
            # INPUT REPO
            repo_string="Association-Analytics/Absorb-LMS-integration-pipeline",
            branch="main",
            connection_arn="[codestarconn]"
           
        )
        # Enter your source system
        sourceSystem = "absorb-lms"

        
        github_credentials = codebuild.GitHubSourceCredentials(self,"CodeBuildGitHubCred",
                                                               access_token=SecretValue.secrets_manager("gh-access-tok"))


        githubUserName = CfnParameter(self,"githubUserName",
                                        type="String",
                                        description="Github Username",
                                        default="Association-Analytics",)
        # githubUserName = "nbtribe"
        githubRepoName = CfnParameter(self,"githubRepoName",
                                        type="String",
                                        description="Github Repo Name",
                                        default="Absorb-LMS-integration-pipeline",)
        # githubRepoName = "devops_pipeline_nb"
        githubSecretName = CfnParameter(self,"githubSecretName",
                                        type="String",
                                        description="Github Secret Name",
                                        default="gh-access-tok",)
        # githubSecretName = "github-token"
        # githubAccessToken = codebuild.BuildEnvironmentVariable(value=os.environ['GITHUB_ACCESS_TOKEN'])

        # IMAGE_REPO_URI = CfnParameter(self,"image_repo_uri",
        #                                 type="String",
        #                                 description="Image Repo URI",
        #                                 default=,)
        
        region = CfnParameter(self,"region",
                                        type="String",
                                        description="region",
                                        default='us-east-1',)
        
        ecrRepo = ecr.Repository(self, "ecrRepo",
                                         repository_name=f"{sourceSystem}-integration",
                                                                             
                                         
                                         )
        
        """If creating a new task role, uncomment the following lines:"""

        # taskRole = iam.Role(self, "taskRole",
        #                     role_name="ecs-task-rolev2",
        #                     assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),)
        


        
        
        # executionRolePolicy  =  iam.PolicyStatement(
        #                                 effect= iam.Effect.ALLOW,
        #                                 resources= ['*'],
        #                                 actions =[
        #                                     "ecr:GetAuthorizationToken",
        #                                     "ecr:BatchCheckLayerAvailability",
        #                                     "ecr:GetDownloadUrlForLayer",
        #                                     "ecr:GetRepositoryPolicy",
        #                                     "ecr:DescribeRepositories",
        #                                     "ecr:ListImages",
        #                                     "ecr:DescribeImages",
        #                                     "ecr:BatchGetImage",
        #                                     "ecr:InitiateLayerUpload",
        #                                     "ecr:UploadLayerPart",
        #                                     "ecr:CompleteLayerUpload",
        #                                     "ecr:PutImage"
        #                                 ]
        #       
        # 
        # )
        
        """Use existing roles for task role and execution"""
        
        
        ecs_role = iam.Role.from_role_arn(self, "existingECSRole",
                                  "arn:aws:iam::009885916296:role/ecsTaskExecutionRole_v2",
                                  mutable=False)
        
        taskDef = ecs.FargateTaskDefinition(self, "taskDef",
                                            task_role=ecs_role,
                                            execution_role=ecs_role,
                                            family= "absorb-lms-task-def",
                                            runtime_platform = {
                                                "cpu_architecture": ecs.CpuArchitecture.X86_64,
                                                "operating_system_family": ecs.OperatingSystemFamily.LINUX
                                            },
                                           
        )
                                            
                                            
                                            
                                            
                                            
                                            
                                            
                                            
        # taskDef.add_to_execution_role_policy(executionRolePolicy)

        baseImage = ecrRepo.repository_uri,
        container = taskDef.add_container("container",
                                          container_name=f"{sourceSystem}",
                                          
                                            # image=ecs.ContainerImage.from_registry(baseImage),
                                            image=ecs.ContainerImage.from_registry("914009102700.dkr.ecr.us-east-1.amazonaws.com/absorb-lms-integration:latest"),
                                            memory_limit_mib=512,
                                            cpu=100,
                                            essential=True,
                                            
                                            logging = ecs.LogDrivers.aws_logs(
                                                stream_prefix="ecs",
                                                log_group=logs.LogGroup(
                                                    self,
                                                    "ecs-log-group",
                                                    log_group_name=f"/ecs/{sourceSystem}-integration",
                                                
                                               
                                                ) )
        )
                                            
                                                                       
                                            
        
        container.add_port_mappings(ecs.PortMapping(container_port=80))


        githubSource = codebuild.Source.git_hub(
            owner=githubUserName.value_as_string,
            
            repo=githubRepoName.value_as_string,
            webhook=True,
            
            webhook_filters= [
                codebuild.FilterGroup.in_event_of(
                    codebuild.EventAction.PUSH
                ).and_branch_is('main')
            ]
        )

        # codebuild - project

        project = codebuild.Project(self, "project",
                                    project_name=self.stack_name,
                                    
                                    source=githubSource,

                                    environment= codebuild.BuildEnvironment(
                                        build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                                        privileged=True,
                                        compute_type=codebuild.ComputeType.LARGE,
                                        
                                        environment_variables={
                                            # "GITHUB_USER_NAME" : {codebuild.BuildEnvironmentVariable(
                                            #     type=codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                                            #     value=githubUserName.value_as_string)},
                                            # "GITHUB_REPO_NAME" : {codebuild.BuildEnvironmentVariable(
                                            #     type=codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                                            #     value=githubRepoName.value_as_string)},
                                            # "GITHUB_SECRET_NAME" : {codebuild.BuildEnvironmentVariable(
                                            #      type=codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                                            #     value=githubRepoName.value_as_string)},
                                            # "GITHUB_SECRET_NAME" : {codebuild.BuildEnvironmentVariable(
                                            #        type=codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                                            #         value=githubSecretName.value_as_string)},
                                            "REGION" : codebuild.BuildEnvironmentVariable(value="us-east-1"),
                                            "IMAGE_REPO_NAME" : codebuild.BuildEnvironmentVariable(value=ecrRepo.repository_name),
                                            "IMAGE_TAG" : codebuild.BuildEnvironmentVariable(value="latest"),
                                            "IMAGE_REPO_URI" :codebuild.BuildEnvironmentVariable(value=ecrRepo.repository_uri),
                                            
                                           

                                        },
                                    ),
                                    build_spec=codebuild.BuildSpec.from_asset("absorb_lms_integration_pipeline/_app/buildspec.yml"),
        )
        
       
 
        #  ***pipeline actions***

        sourceOutput =  pipeline.Artifact()
        buildOutput =  pipeline.Artifact()
        nameOfGithubPersonTokenParameterAsString = githubSecretName.value_as_string
        sourceAction = pipelineactions.GitHubSourceAction(
            action_name="github_source",
            owner=githubUserName.value_as_string,
            repo=githubRepoName.value_as_string,
            branch="main",
            oauth_token=SecretValue.secrets_manager(nameOfGithubPersonTokenParameterAsString),
            
            output=sourceOutput,
)
 
 
        buildAction = pipelineactions.CodeBuildAction(
            action_name="codebuild_action",
            project=project,
            input=sourceOutput,
            outputs=[buildOutput],

        )
        

        manualApprovalAction = pipelineactions.ManualApprovalAction(
            action_name="manual_approval_action",
        )

        # pipeline stages
        pipeline.Pipeline(self,"ecrpipeline",
                          
                            stages=[
                                {
                                    "stageName": "Source",
                                    "actions": [sourceAction],

                                },
                                {
                                    "stageName": "Build",
                                    "actions": [buildAction],

                                },
                                {
                                    "stageName": "Approval",
                                    "actions":[manualApprovalAction],

                                }

                            ]

                                    )
        
        ecrRepo.grant_pull_push(project.role)


        CfnOutput(self, "image", value=f"{ecrRepo.repository_uri}:latest")
        CfnOutput(self, "repo_name", value=f"{ecrRepo.repository_name}")
        CfnOutput(self, "region1", value=f"{os.getenv('CDK_DEFAULT_REGION')}")
