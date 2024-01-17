from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    CfnOutput
)
import fs

import os.path as path

dirname = path.dirname(__file__)

from constructs import Construct

class NetworkingSetStaticIpLambdaWithNatStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # **********IMPORTANT --> MUST Create the KeyPair for this CDK Deploy to work

        # Create VPC
        vpc = ec2.Vpc(self, "VPC",
                      ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
                      max_azs=2,
                      nat_gateways=0,
                      subnet_configuration=[
                          ec2.SubnetConfiguration(
                          subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                          cidr_mask=28,
                          name="PrivateSubnet"),
                          ec2.SubnetConfiguration(
                              subnet_type=ec2.SubnetType.PUBLIC,
                              cidr_mask=28,
                              name="PublicSubnet")
                          ]
        )
        

        # Create Security Grp
        public_sg = ec2.SecurityGroup(self, "publicSecurityGroup",
                                      vpc=vpc,
                                      description="SG for Public Endpoints",
                                      allow_all_outbound=True)
        
        public_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH (TCP port 22)",
            )
        public_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP (TCP port 80)",
            )
        public_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow HTTPS (TCP port 443)",
            )

        # Create NAT Instance
        # Create the KeyPair EC2 and get.pem file
        custNat = ec2.Instance(self, "custom-NAT-instance",
                                vpc=vpc,
                                instance_type=ec2.InstanceType("t3.micro"),
                                machine_image=ec2.AmazonLinuxImage(
                                    generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2023
                                ),
                                key_name="nb-test-keypair", # replace with existing KP
                                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                security_group=public_sg,
                                source_dest_check=False,
                                associate_public_ip_address=True, # assigns public IPs to subnets

                                )
        
        initScriptPath = path.join(dirname, 'initScripts.sh')
        with open(initScriptPath, 'r') as f:
            userData = f.read()
        
        # userData = open(initScriptPath,'utf-8','r')
        custNat.add_user_data(userData)

        # RouteSetup
        # pvtSubnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets
        pvtSubnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
        # Add route to private subnets
        (pvtSubnets.subnets[0]).add_route("NAT-route-0",
                                            router_id=custNat.instance_id,
                                            router_type=ec2.RouterType.INSTANCE,
                                            destination_cidr_block="0.0.0.0/0")
        (pvtSubnets.subnets[1]).add_route("NAT-route-1",
                                            router_id=custNat.instance_id,
                                            router_type=ec2.RouterType.INSTANCE,
                                            destination_cidr_block="0.0.0.0/0")

        
        # Assign elastic IPs to NAT instances
        elasticIP = ec2.CfnEIP(self, "elasticIP",)
        ec2.CfnEIPAssociation(self, "eipAssociation",
                              eip=elasticIP.ref,
                              instance_id=custNat.instance_id)
        
        # Create Lambda Function
        lambda_function = _lambda.Function(
                                            self, "LambdaFunction",
                                            vpc=vpc,
                                            runtime=_lambda.Runtime.PYTHON_3_9,
                                            handler="test.lambda_handler",
                                            code=_lambda.Code.from_asset(path.join(dirname, '..\lambda')),
                                            timeout=Duration.seconds(10)
                                        
                                            )
        
        
        VPC_Output = CfnOutput(self, "VPCID",
                              value=vpc.vpc_id,
                              description="VPC ID",
                              export_name="VPCID")
        
                            
                    

