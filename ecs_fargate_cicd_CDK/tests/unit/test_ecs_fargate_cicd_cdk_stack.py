import aws_cdk as core
import aws_cdk.assertions as assertions

from ecs_fargate_cicd_cdk.ecs_fargate_cicd_cdk_stack import EcsFargateCicdCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ecs_fargate_cicd_cdk/ecs_fargate_cicd_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EcsFargateCicdCdkStack(app, "ecs-fargate-cicd-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
