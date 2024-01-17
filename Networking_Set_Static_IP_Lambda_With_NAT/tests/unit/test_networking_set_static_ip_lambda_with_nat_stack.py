import aws_cdk as core
import aws_cdk.assertions as assertions

from networking_set_static_ip_lambda_with_nat.networking_set_static_ip_lambda_with_nat_stack import NetworkingSetStaticIpLambdaWithNatStack

# example tests. To run these tests, uncomment this file along with the example
# resource in networking_set_static_ip_lambda_with_nat/networking_set_static_ip_lambda_with_nat_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = NetworkingSetStaticIpLambdaWithNatStack(app, "networking-set-static-ip-lambda-with-nat")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
