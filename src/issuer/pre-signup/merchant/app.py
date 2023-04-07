import os

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from pyqldb.driver.qldb_driver import QldbDriver
from rewards_dao import RewardsDAO, Driver

tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")


@tracer.capture_method
def signup_confirmation(event: dict, context: LambdaContext, qldb_driver: Driver = None):
    metrics.add_metric(name="SignupConfirmationInvocations", unit=MetricUnit.Count, value=1)
    user_sub = event.get("userName")

    def execute_signup_confirmation(dao: RewardsDAO):
        dao.insert_balance(sub=user_sub, key=f"user-initialize-{user_sub}")

    # Query the table
    RewardsDAO(driver=qldb_driver).execute_transaction(lambda dao: execute_signup_confirmation(dao))

    # Confirm the user
    event['response']['autoConfirmUser'] = True

    # Set the email as verified if it is in the request
    if 'email' in event['request']['userAttributes']:
        event['response']['autoVerifyEmail'] = True

    # Set the phone number as verified if it is in the request
    if 'phone_number' in event['request']['userAttributes']:
        event['response']['autoVerifyPhone'] = True

    # Return to Amazon Cognito
    return event


# Enrich logging with contextual information from Lambda
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
# Adding tracer
# See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/
@tracer.capture_lambda_handler
# ensures metrics are flushed upon request completion/failure and capturing ColdStart metric
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return signup_confirmation(event=event, context=context)
