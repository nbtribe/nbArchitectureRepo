import aws_cdk as core
import aws_cdk.assertions as assertions

from ms_teams_etl_alert_bot.ms_teams_etl_alert_bot_stack import MsTeamsEtlAlertBotStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ms_teams_etl_alert_bot/ms_teams_etl_alert_bot_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MsTeamsEtlAlertBotStack(app, "ms-teams-etl-alert-bot")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
