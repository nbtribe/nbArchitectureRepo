import aws_cdk as core
import aws_cdk.assertions as assertions

from data_analytics_capture_clickstream_solution.data_analytics_capture_clickstream_solution_stack import DataAnalyticsCaptureClickstreamSolutionStack

# example tests. To run these tests, uncomment this file along with the example
# resource in data_analytics_capture_clickstream_solution/data_analytics_capture_clickstream_solution_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DataAnalyticsCaptureClickstreamSolutionStack(app, "data-analytics-capture-clickstream-solution")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
