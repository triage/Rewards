import os

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from pyqldb.driver.qldb_driver import QldbDriver
from pyqldb.config.retry_config import RetryConfig

tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")


@tracer.capture_method
def signup_confirmation(event: dict):
    # adding custom metrics
    # See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/metrics/
    metrics.add_metric(name="SignupConfirmationInvocations", unit=MetricUnit.Count, value=1)

    # structured log
    # See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/logger/
    logger.info("LedgerStore API - issuer/pre-signup/merchant HTTP 200")
    user_sub = event.get("request.userAttributes.sub")
    retry_config = RetryConfig(retry_limit=3)
    qldb_driver = QldbDriver(ledger_name=os.environ.get("LEDGER_NAME"), retry_config=retry_config)

    def execute_signup_confirmation(transaction_executor):
        # initialize the user
        QLDBHelper.insert_balance(sub=user_sub, key=f"user-initialize-{user_sub}")

    # Query the table
    qldb_driver.execute_lambda(lambda executor: execute_signup_confirmation(executor))

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
    return signup_confirmation(event, context)
