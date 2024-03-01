import aws_cdk as core
import aws_cdk.assertions as assertions

from auto_integration_deployments.auto_integration_deployments_stack import AutoIntegrationDeploymentsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in auto_integration_deployments/auto_integration_deployments_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AutoIntegrationDeploymentsStack(app, "auto-integration-deployments")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
