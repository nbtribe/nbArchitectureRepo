from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    CfnParameter,
    SecretValue,
    RemovalPolicy,
    CfnOutput,
    aws_logs as logs
)
from constructs import Construct

class EcsFargateCicdCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # execute line = cdk deploy --parameters GitHubUserName={gh_username} --parameters DockerUsername={dckr_username} --parameters DockerPassword={dckr_pwd}

        ACCOUNT = self.account
        REGION = self.region


        DOCKER_USERNAME = CfnParameter(self, "DockerUsername", type="String",
                                       description="Docker Username to use for the pipeline",)
        docker_user = DOCKER_USERNAME.value_as_string
        DOCKER_PASSWORD = CfnParameter(self, "DockerPassword", type="String",
                                       description="Docker Password to use for the pipeline",)
        docker_pwd = DOCKER_PASSWORD.value_as_string

        source_system_param= CfnParameter(self, "SourceSystem", type="String",
                                     description="Source System to use for the pipeline",
                                     default="extract",)
        source_system = source_system_param.value_as_string

        githubRepo = CfnParameter(self, "GitHubRepo", type="String",
                                  description="GitHub Repo to use for the pipeline",
                                  default="test_extract")
        
        githubUserName = CfnParameter(self, "GitHubUserName", type="String",
                                      description="GitHub User Name to use for the pipeline",
        )

        githubAccessToken = CfnParameter(self, "GitHubAccessToken", type="String",
                                         description="GitHub Access Token to use for the pipeline",
                                         default="/githubAccessToken")
        
        
        ecrRepo = ecr.Repository(self, "EcrRepo",
                                 repository_name=f"{source_system}",
                                 removal_policy=RemovalPolicy.DESTROY,
                                 )
        
        vpc = ec2.Vpc(
            self, "MyVpc",
            max_azs=3,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                    )
            ]
                )
        
        cluster = ecs.Cluster(
            self, "Cluster",
            vpc=vpc,
            )
        # ecs exec role
        task_role = iam.Role(self, "TaskRole",
                             assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"))
        
        task_role.add_to_policy(iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
            resources=["*"],
            actions=["ecr:getauthorizationtoken",
                     "ecr:batchchecklayeravailability",
                     "ecr:getdownloadurlforlayer",
                     "ecr:batchgetimage",
                     "logs:createlogstream",
                     "logs:putlogevents",
                     "ecr:GetRepositoryPolicy",
                     "ecr:DescribeRepositories",
                     "ecr:ListImages",
                     "ecr:DescribeImages",
                     "ecr:BatchGetImage",
                     "ecr:InitiateLayerUpload",
                     "ecr:UploadLayerPart",
                     "ecr:CompleteLayerUpload",
                     "ecr:PutImage"]  
        )
        )

        # create task definition
        task_definition = ecs.FargateTaskDefinition(
            self, "TaskDefinition",
            cpu=1024,
            memory_limit_mib=2048,
            task_role=task_role,
            execution_role=task_role,
            family= f"{source_system}-task-def",
            runtime_platform = {
                    "cpu_architecture": ecs.CpuArchitecture.X86_64,
                    "operating_system_family": ecs.OperatingSystemFamily.LINUX
                },
            )
        
        container = task_definition.add_container("container",
                                                  container_name=f"{source_system}",
                                                  image=ecs.ContainerImage.from_registry(f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/{source_system}:latest"),
                                                  memory_limit_mib=512,
                                                  cpu=100,
                                                  essential=True,
                                                  logging = ecs.LogDrivers.aws_logs(
                                                      stream_prefix="ecs",
                                                      log_group=logs.LogGroup(
                                                          self,
                                                          "ecs-log-group",
                                                          log_group_name=f"/ecs/{source_system}",
                                                          retention=logs.RetentionDays.ONE_WEEK,
                                                          removal_policy=RemovalPolicy.DESTROY,
                                                          )
                                                  )
        )

        container.add_port_mappings(ecs.PortMapping(container_port=80)
                                    )

        gitHubSource = codebuild.Source.git_hub(

            owner=githubUserName.value_as_string,
            repo=githubRepo.value_as_string,
            webhook=True,
            webhook_filters=[
                            codebuild.FilterGroup.in_event_of(codebuild.EventAction.PUSH).and_branch_is("main")
                ]
        )

        project = codebuild.Project(
            self, "CodeBuild_Project",
            project_name=f"{source_system}_pipeline",
            source=gitHubSource,
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
                privileged=True
            ),
            environment_variables={
                "CLUSTER_NAME" : codebuild.BuildEnvironmentVariable(value=cluster.cluster_name),
                "REGION" : codebuild.BuildEnvironmentVariable(value=REGION),
                "IMAGE_REPO_NAME" : codebuild.BuildEnvironmentVariable(value=ecrRepo.repository_name),
                "IMAGE_TAG" : codebuild.BuildEnvironmentVariable(value="latest"),
                "IMAGE_REPO_URI" : codebuild.BuildEnvironmentVariable(value=ecrRepo.repository_uri),
                "DOCKER_USERNAME" : codebuild.BuildEnvironmentVariable(value=docker_user),
                "DOCKER_PASSWORD" : codebuild.BuildEnvironmentVariable(value=docker_pwd)


            },
            badge=True,
            build_spec=codebuild.BuildSpec.from_asset("./assets/buildspec.yml")
        )

        ecrRepo.grant_pull_push(project.role)
                                

        # PIPELINE STEPS
        sourceOutput = codepipeline.Artifact()
        buildOutput = codepipeline.Artifact()
        
        githubAccessTokenString = githubAccessToken.value_as_string

        sourceAction = codepipeline_actions.GitHubSourceAction(
            action_name="Github_Source",
            owner=githubUserName.value_as_string,
            repo=githubRepo.value_as_string,
            branch="main",
            oauth_token=SecretValue.secrets_manager(githubAccessTokenString),
            output=sourceOutput,
        )

        buildAction = codepipeline_actions.CodeBuildAction(
            action_name="CodeBuild",
            project=project,
            input=sourceOutput,
            outputs=[buildOutput],
        )

        manualApprovalAction = codepipeline_actions.ManualApprovalAction(
            action_name="Approve_Build",
            additional_information="Approve to Proceed with Deployment",
        )


        # Pipeline Stages
        pipeline = codepipeline.Pipeline(
            self, "Pipeline",
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[sourceAction],
                ),
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[buildAction],
                ),
                codepipeline.StageProps(
                    stage_name="Approve_Build",
                    actions=[manualApprovalAction],
                )

            ],
        )

        ecrRepo.grant_pull_push(pipeline.role)

        project.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=[cluster.cluster_arn],
            actions=["ecs:DescribeServices",
                    "ecr:getauthorizationtoken",
                    "ecr:batchchecklayeravailability",
                    "ecr:batchgetimage",
                    "ecr:getdownloadurlforlayer"]
                    )
                    )
        
        CfnOutput(self, "ECRRepoName", value=f"{ecrRepo.repository_uri}:latest")
        CfnOutput(self, "Docker UserName", value=DOCKER_USERNAME.value_as_string)
        CfnOutput(self, "Docker Password", value=DOCKER_PASSWORD.value_as_string)