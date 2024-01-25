import aws_cdk as core
import aws_cdk.assertions as assertions

from google_analytics_etl_app_flow_glue.google_analytics_etl_app_flow_glue_stack import GoogleAnalyticsEtlAppFlowGlueStack

# example tests. To run these tests, uncomment this file along with the example
# resource in google_analytics_etl_app_flow_glue/google_analytics_etl_app_flow_glue_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = GoogleAnalyticsEtlAppFlowGlueStack(app, "google-analytics-etl-app-flow-glue")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
