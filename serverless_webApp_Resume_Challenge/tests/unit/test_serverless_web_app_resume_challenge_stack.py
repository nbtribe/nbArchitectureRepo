import aws_cdk as core
import aws_cdk.assertions as assertions

from serverless_web_app_resume_challenge.serverless_web_app_resume_challenge_stack import ServerlessWebAppResumeChallengeStack

# example tests. To run these tests, uncomment this file along with the example
# resource in serverless_web_app_resume_challenge/serverless_web_app_resume_challenge_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ServerlessWebAppResumeChallengeStack(app, "serverless-web-app-resume-challenge")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
