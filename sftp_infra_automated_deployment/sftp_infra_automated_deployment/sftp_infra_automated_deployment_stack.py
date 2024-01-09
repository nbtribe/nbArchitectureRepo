from aws_cdk import (
    # Duration,
    Stack,
    CfnParameter,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_s3_notifications as s3n,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    SecretValue,
    Duration,
    RemovalPolicy
)
from constructs import Construct

import os
import json

class SftpInfraAutomatedDeploymentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
                # Create a CfnParameter for the client acronym
        client_acromym = CfnParameter(self,"ClientAcronym",
                                      type="String",
                                      description="Enter the client acronym",)
        # source_system = CfnParameter(self,"SourceSystem",
        #                               type="String",
        #                               description="Enter the source system",)
        # module = CfnParameter(self,"Module",
        #                               type="String",
        #                               description="Enter the module",)
        # destination_bucket = CfnParameter(self,"DestinationBucket",
        #                                   type="String",
        #                                   description="Enter the destination bucket",)
        # source_bucket = CfnParameter(self,"SourceBucket",
        #                                   type="String",
        #                                   description="Enter the source bucket",)
        # destination_prefix = CfnParameter(self,"DestinationPrefix",
        #                                   type="String",
        #                                   description="Enter the destination prefix",)
        # source_prefix = CfnParameter(self,"SourcePrefix",
        #                                   type="String",
        #                                   description="Enter the source prefix",)
        
        
        x_client_acronym = f"{client_acromym.value_as_string}"
        self.x_client_acronym = self.node.try_get_context('x_client_acronym')
        # x_source_system = f"{source_system.value_as_string}"
        # x_module = f"{module.value_as_string}"
        # x_destination_bucket = f"{destination_bucket.value_as_string}"
        # x_source_bucket = f"{source_bucket.value_as_string}"
        # x_destination_prefix = f"{destination_prefix.value_as_string}"
        # x_source_prefix = f"{source_prefix.value_as_string}"
        
        
        # Fill Out the below params
        SOURCE_SYS = "oas"
        MODULE = "lms"
        DESTINATION_BUCKET ="case-dm-associationanalytics"
        SOURCE_BUCKET = "a2-ftp"
        customer = "case"
        REQUIRED_FILES = "CurrentCourses.csv;UserEnrollments.csv;CreditClaimed.csv;Learners.csv;CourseFeedback.csv;CertifiedUsers.csv;InstructorRatings.csv;CoursePerformance.csv;CourseInTracks.csv;Tracks.csv"
        DEST_PREFIX	= f"data/{MODULE}_{SOURCE_SYS}"
        SOURCE_PREFIX = f"{x_client_acronym}_{SOURCE_SYS}"
        SOURCE_PREFIX_PATH= f"{x_client_acronym}_{SOURCE_SYS}/toprocess"
        
        
        

        
        # existing bucket
        bucket = s3.Bucket.from_bucket_attributes(self, "ExistingBucket",
        bucket_arn = f"arn:aws:s3:::{SOURCE_BUCKET}", 
        )
        
        s3deploy.BucketDeployment(self, "DeployFileStruct",
                                  sources=[s3deploy.Source.asset("assets")],
                                  destination_bucket=bucket,
                                #   destination_key_prefix="ttest_sftp/toprocess",
                                  destination_key_prefix=SOURCE_PREFIX_PATH,
        )
                                  
        

        # lambda role
        lambda_role = iam.Role(self, "LambdaSFTPRole",
                                role_name= f"{customer}_{SOURCE_SYS}_SFTPRole",
                                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                                                  ],
                                )
        
        lambda_role.attach_inline_policy(
                            iam.Policy(self, f"{customer}-{SOURCE_SYS}-lambda-SFTP-policy",
                    
                                        statements=[
                                            iam.PolicyStatement(
                                                effect=iam.Effect.ALLOW,
                                                actions=["s3:DeleteObject","s3:GetObject"],
                                                # resources=[f"arn:aws:s3:::{SOURCE_BUCKET}/{x_client_acronym}_{SOURCE_SYS}/toprocess/*"]
                                                resources=[f"arn:aws:s3:::{SOURCE_BUCKET}/{SOURCE_PREFIX_PATH}/*"]
                                    ),
                                            iam.PolicyStatement(
                                                effect=iam.Effect.ALLOW,
                                                actions=["s3:ListBucket"],
                                                resources=[f"arn:aws:s3:::{SOURCE_BUCKET}",
                                                            # f"arn:aws:s3:::{SOURCE_BUCKET}/{x_client_acronym}_{SOURCE_SYS}/toprocess*"]
                                                            f"arn:aws:s3:::{SOURCE_BUCKET}/{SOURCE_PREFIX}*"]
                                    ),
                                            iam.PolicyStatement(
                                                effect=iam.Effect.ALLOW,
                                                actions=["s3:PutObject"],
                                                # resources=[f"arn:aws:s3:::{DESTINATION_BUCKET}/data/{SOURCE_SYS}*"]
                                                resources=[f"arn:aws:s3:::{DESTINATION_BUCKET}/{DEST_PREFIX}*"]
                                    ),
                                            iam.PolicyStatement(
                                                effect=iam.Effect.ALLOW,
                                                actions=["s3:PutObject","s3:GetObject"],
                                                resources=[f"arn:aws:s3:::{DESTINATION_BUCKET}/scripts/*"]
                                    )
                                    ]
       ))
                                                   
        
        # Create lambda function
        sftp_lambda = lambda_.Function(self, "SFTPProcessFilesAuto",
                                       function_name=f"{x_client_acronym}-{SOURCE_SYS}-SFTPProcessFilesAuto",
                                        runtime=lambda_.Runtime.PYTHON_3_10,
                                        handler="process_files.lambda_handler",
                                        code=lambda_.Code.from_asset(f"src/lambda/{SOURCE_SYS}"),
                                        role=lambda_role,
                                        timeout=Duration.seconds(300),
                                        memory_size=1024,
                                        environment={"DESTINATION_BUCKET": DESTINATION_BUCKET,
                                                     "DEST_PREFIX" : DEST_PREFIX,
                                                     "CUSTOMER": f"{x_client_acronym}",
                                                     "SOURCE_BUCKET": SOURCE_BUCKET,
                                                     "SOURCE_PREFIX": SOURCE_PREFIX_PATH,
                                                     "SOURCE_SYS": f"{MODULE}_{SOURCE_SYS}",
                                                     "REQUIRED_FILES": REQUIRED_FILES
                                                     },
                                        
                                       
        )
        # Event Bucket Notification fires the processing lambda
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                      s3n.LambdaDestination(sftp_lambda),
                                    s3.NotificationKeyFilter(prefix=f"{SOURCE_PREFIX_PATH}/"),
                                      s3.NotificationKeyFilter(suffix=".csv")
                                      )


        # Create the Secret in Secrets Manager
        sftp_secret = secretsmanager.Secret(self, "Secret",
                                            secret_name=f"SFTP/{x_client_acronym}_{SOURCE_SYS}",
                                            description=f"SFTP credentials for {x_client_acronym} {MODULE}_{SOURCE_SYS}",
                                            removal_policy=RemovalPolicy.DESTROY,
                                            generate_secret_string=secretsmanager.SecretStringGenerator(
                                                secret_string_template= json.dumps({"Role":f"arn:aws:iam::009885916296:role/a2_sftp_{x_client_acronym}_{MODULE}_{SOURCE_SYS}_role","HomeDirectory":f"/{SOURCE_BUCKET}/{x_client_acronym}_{SOURCE_SYS}","PublicKey1":""}),
                                                generate_string_key='Password',
                                                include_space=False
                                            )
                                            )
        
        
        
        # Probably have to create the Role that Allows Transfer Family to call AWS services here
        transfer_fam_role = iam.Role(self, "Transfer Family Role",
                                role_name = f"a2_sftp_{x_client_acronym}_{MODULE}_{SOURCE_SYS}_role",
                                
                                assumed_by=iam.ServicePrincipal("transfer.amazonaws.com"),

                                )
    
        # Create the trasfer family policy 
        transfer_policy = iam.Policy(self, f"{customer}-{SOURCE_SYS}-TransferPolicy",
                                     
        )
        # add to the policy
        transfer_policy.add_statements(
            iam.PolicyStatement(
                sid = "AllowListingOfUserFolder",
                effect=iam.Effect.ALLOW,
                actions=["s3:ListBucket"],
                resources=[f"arn:aws:s3:::{SOURCE_BUCKET}"],
                conditions={
                    "StringLike": {
                        "s3:prefix": [f"{SOURCE_PREFIX}/*",
                                      f"{SOURCE_PREFIX}"]
                    }}
                
            )
        )
        # add to the policy
        transfer_policy.add_statements(
            iam.PolicyStatement(
                sid = "HomeDirObjectAccess",
                effect=iam.Effect.ALLOW,
                actions=["s3:PutObject",
                         "s3:GetObject",
                         "s3:DeleteObjectVersion",
                         "s3:DeleteObject",
                         "s3:GetObjectVersion"],
                resources=[f"arn:aws:s3:::{SOURCE_BUCKET}/{SOURCE_PREFIX}*"],
                # conditions={
                #     "StringLike": {
                #         "s3:prefix": [f"{SOURCE_PREFIX}/*",
                #                       f"{SOURCE_PREFIX}"]
                #     }}
                
            )
        )
        
        # Attach Transfer policy to the Transfer Family role
        transfer_fam_role.attach_inline_policy(transfer_policy)
        
        
        # ^^THIS HAS TO ATTACH DIRECTKY TO THE Access USER
                # existing user
        existing_user = iam.User.from_user_attributes(self, "ImportedUser",
                        # user_arn=f"arn:aws:iam::009885916296:user/{x_client_acronym}AccessUser",
                        user_arn = "arn:aws:iam::009885916296:user/CASEExtractProgram"
        )
        # Attaching policy to existing Access User
        transfer_policy.attach_to_user(existing_user)

        
    #     existing_user.attach_inline_policy(
    #                         iam.Policy(self, f"a2_SFTP_{client_acromym}_policy",
                                    
    #                                     statements=[
    #                                         iam.PolicyStatement(
    #                                             # sid = "AllowListingOfUserFolder",
    #                                             effect=iam.Effect.ALLOW,
    #                                             actions=["s3:ListBucket"],
    #                                             resources=[f"arn:aws:s3:::{SOURCE_BUCKET}"],
    #                                 ),
    #                                         iam.PolicyStatement(
    #                                             effect=iam.Effect.ALLOW,
    #                                             actions=["s3:ListBucket"],
    #                                             resources=[f"arn:aws:s3:::{SOURCE_BUCKET}",
    #                                                         # f"arn:aws:s3:::{SOURCE_BUCKET}/{x_client_acronym}_{SOURCE_SYS}/toprocess*"]
    #                                                         f"arn:aws:s3:::{SOURCE_BUCKET}/{SOURCE_PREFIX}*"]
    #                                 ),
    #                                         iam.PolicyStatement(
    #                                             effect=iam.Effect.ALLOW,
    #                                             actions=["s3:PutObject"],
    #                                             # resources=[f"arn:aws:s3:::{DESTINATION_BUCKET}/data/{SOURCE_SYS}*"]
    #                                             resources=[f"arn:aws:s3:::{DESTINATION_BUCKET}/{DEST_PREFIX}*"]
    #                                 ),
    #                                         iam.PolicyStatement(
    #                                             effect=iam.Effect.ALLOW,
    #                                             actions=["s3:PutObject","s3:GetObject"],
    #                                             resources=[f"arn:aws:s3:::{DESTINATION_BUCKET}/scripts/*"]
    #                                 )
    #                                 ]
    #    ))