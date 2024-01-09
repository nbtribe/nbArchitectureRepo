import aws_cdk as core
import aws_cdk.assertions as assertions

from sftp_infra_automated_deployment.sftp_infra_automated_deployment_stack import SftpInfraAutomatedDeploymentStack

# example tests. To run these tests, uncomment this file along with the example
# resource in sftp_infra_automated_deployment/sftp_infra_automated_deployment_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SftpInfraAutomatedDeploymentStack(app, "sftp-infra-automated-deployment")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
