import aws_cdk as core
import aws_cdk.assertions as assertions

from fargate_ecs_cicd_cdk.fargate_ecs_cicd_cdk_stack import FargateEcsCicdCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in fargate_ecs_cicd_cdk/fargate_ecs_cicd_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = FargateEcsCicdCdkStack(app, "fargate-ecs-cicd-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
