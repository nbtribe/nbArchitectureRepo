#!/usr/bin/env python3
import os

import aws_cdk as cdk

from auto_integration_deployments.auto_integration_deployments_stack import AutoIntegrationDeploymentsStack
from auto_integration_deployments.integration_code_pipeline import IntegrationCodePipeline

# env = cdk.Environment(account="0000000",region="us-east-1")
app = cdk.App()
AutoIntegrationDeploymentsStack(app, "AutoIntegrationDeploymentsStack",
                                env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
                                
 )


IntegrationCodePipeline(app, f"IntegrationCodePipeline",
                        env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))
app.synth()

