import aws_cdk as core
import aws_cdk.assertions as assertions

from migrate_existing_s_ftp_clients_to_cloud_infra.migrate_existing_s_ftp_clients_to_cloud_infra_stack import MigrateExistingSFtpClientsToCloudInfraStack

# example tests. To run these tests, uncomment this file along with the example
# resource in migrate_existing_s_ftp_clients_to_cloud_infra/migrate_existing_s_ftp_clients_to_cloud_infra_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MigrateExistingSFtpClientsToCloudInfraStack(app, "migrate-existing-s-ftp-clients-to-cloud-infra")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
