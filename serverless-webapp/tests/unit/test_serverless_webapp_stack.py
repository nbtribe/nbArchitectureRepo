import aws_cdk as core
import aws_cdk.assertions as assertions

from serverless_webapp.serverless_webapp_stack import ServerlessWebappStack

# example tests. To run these tests, uncomment this file along with the example
# resource in serverless_webapp/serverless_webapp_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ServerlessWebappStack(app, "serverless-webapp")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
