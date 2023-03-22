import os

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from pyqldb.driver.qldb_driver import QldbDriver
from pyqldb.config.retry_config import RetryConfig

from src.qldb.qldp_helper import QLDBHelper

tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")


@tracer.capture_method
def signup_confirmation(event: dict, context: LambdaContext):
    # adding custom metrics
    # See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/metrics/
    metrics.add_metric(name="SignupConfirmationInvocations", unit=MetricUnit.Count, value=1)

    # structured log
    # See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/logger/
    logger.info("LedgerStore API - HTTP 200")
    user_sub = event.get("request.userAttributes.sub")
    retry_config = RetryConfig(retry_limit=3)
    qldb_driver = QldbDriver(ledger_name=os.environ.get("LEDGER_NAME"), retry_config=retry_config)
    amount = int(os.environ.get("USER_SIGNUP_REWARD"))
    merchant_sub = "ISSUER"
    key = f"POST-SIGNUP-{user_sub}"
    description = "Signup bonus"

    def execute_signup_confirmation(transaction_executor):
        # initialize the user
        QLDBHelper.insert_balance(sub=user_sub, key=f"user-initialize-{user_sub}")

        # insert into a transaction for the user
        QLDBHelper.insert_transaction(values={
            "id": "{key}-user".format(key=key),
            "key": key,
            "sub": user_sub,
            "amount": amount,
            "description": description
        }, executor=transaction_executor)

        # insert a transaction for the merchant
        QLDBHelper.insert_transaction(values={
            "id": "{key}-merchant".format(key=key),
            "key": key,
            "sub": merchant_sub,
            "amount": -amount,
            "description": description,
            "user_sub": user_sub,
        }, executor=transaction_executor)

        # update the balance to the new amount
        QLDBHelper.update_balance(sub=user_sub, key=key, balance=amount, executor=transaction_executor)

    # Query the table
    qldb_driver.execute_lambda(lambda executor: execute_signup_confirmation(executor))

    return {"status": "OK"}


# Enrich logging with contextual information from Lambda
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
# Adding tracer
# See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/
@tracer.capture_lambda_handler
# ensures metrics are flushed upon request completion/failure and capturing ColdStart metric
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return signup_confirmation(event, context)
